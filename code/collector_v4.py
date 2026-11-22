#!/usr/bin/env python3
"""Concurrent Redfish telemetry collector with explicit poll-quality metadata."""
import argparse
import csv
import getpass
import os
import time
import threading
import atexit
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FIELDS = [
    "timestamp", "sensor_id", "sensor_name", "reading", "units",
    "health", "state", "lower_caution", "lower_critical",
    "upper_caution", "upper_critical", "poll_id",
    "poll_start_timestamp", "poll_duration_seconds", "poll_status",
    "request_status", "sensor_url", "error",
]


# Each executor thread owns its own persistent Session.
_THREAD_LOCAL = threading.local()
_SESSIONS = []
_SESSIONS_LOCK = threading.Lock()


def get_worker_session(username, password):
    if not hasattr(_THREAD_LOCAL, "session"):
        session = requests.Session()
        session.auth = (username, password)
        session.verify = False
        session.headers.update({"Accept": "application/json"})
        _THREAD_LOCAL.session = session

        with _SESSIONS_LOCK:
            _SESSIONS.append(session)

    return _THREAD_LOCAL.session


def close_worker_sessions():
    with _SESSIONS_LOCK:
        sessions = list(_SESSIONS)
        _SESSIONS.clear()

    for session in sessions:
        session.close()


atexit.register(close_worker_sessions)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def get_json(session, url, timeout):
    response = session.get(url, timeout=timeout, verify=False)
    response.raise_for_status()
    return response.json()


def find_sensor_collection(session, base_url, timeout):
    chassis = get_json(session, urljoin(base_url, "/redfish/v1/Chassis"), timeout)
    members = chassis.get("Members", [])
    if not members:
        raise RuntimeError("No Redfish chassis found")

    chassis_url = urljoin(base_url, members[0]["@odata.id"])
    chassis_data = get_json(session, chassis_url, timeout)
    sensors_link = (chassis_data.get("Sensors") or {}).get("@odata.id")
    if not sensors_link:
        raise RuntimeError("Chassis does not expose a Sensors collection")
    return urljoin(base_url, sensors_link)


def read_sensor(sensor_info, username, password, timeout):
    index, sensor_url = sensor_info

    try:
        # Reuse the persistent Session belonging to this executor thread.
        session = get_worker_session(username, password)
        sensor = get_json(session, sensor_url, timeout)

        status = sensor.get("Status") or {}
        thresholds = sensor.get("Thresholds") or {}

        def threshold_value(name):
            return (thresholds.get(name) or {}).get("Reading", "")

        return index, {
            "sensor_id": sensor.get("Id", ""),
            "sensor_name": sensor.get("Name", ""),
            "reading": sensor.get("Reading", ""),
            "units": sensor.get("ReadingUnits", ""),
            "health": status.get("Health", ""),
            "state": status.get("State", ""),
            "lower_caution": threshold_value("LowerCaution"),
            "lower_critical": threshold_value("LowerCritical"),
            "upper_caution": threshold_value("UpperCaution"),
            "upper_critical": threshold_value("UpperCritical"),
            "request_status": "success",
            "sensor_url": sensor_url,
            "error": "",
        }

    except Exception as exc:
        fallback_id = sensor_url.rstrip("/").split("/")[-1]
        return index, {
            "sensor_id": fallback_id,
            "sensor_name": "",
            "reading": "",
            "units": "",
            "health": "",
            "state": "",
            "lower_caution": "",
            "lower_critical": "",
            "upper_caution": "",
            "upper_critical": "",
            "request_status": "failure",
            "sensor_url": sensor_url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main():
    parser = argparse.ArgumentParser(
        description="Concurrent Redfish collector with persistent thread-local sessions"
    )
    parser.add_argument("--url", default="https://127.0.0.1:2445")
    parser.add_argument("--username", default="root")
    parser.add_argument("--output", default="data/raw/redfish_telemetry_v4.csv")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Target start-to-start polling interval in seconds")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args()

    if args.interval <= 0 or args.count <= 0 or args.workers <= 0 or args.timeout <= 0:
        parser.error("--interval, --count, --workers, and --timeout must be positive")
    if os.path.exists(args.output):
        parser.error(f"Output already exists; choose another path: {args.output}")

    password = getpass.getpass("BMC password: ")
    base_url = args.url.rstrip("/") + "/"

    # Discover the sensor list once before starting the timed polling loop.
    with requests.Session() as session:
        session.auth = (args.username, password)
        session.verify = False
        session.headers.update({"Accept": "application/json"})
        collection_url = find_sensor_collection(session, base_url, args.timeout)
        collection = get_json(session, collection_url, args.timeout)

    sensor_urls = [
        urljoin(base_url, member["@odata.id"].lstrip("/"))
        for member in collection.get("Members", [])
        if member.get("@odata.id")
    ]
    if not sensor_urls:
        raise RuntimeError("No sensor members found in Redfish Sensors collection")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    worker_count = min(args.workers, len(sensor_urls))
    print(f"Found {len(sensor_urls)} sensors; using {worker_count} workers.")
    print(f"Collecting {args.count} polls; target interval={args.interval}s; timeout={args.timeout}s.")

    # Exclusive creation protects every existing dataset from accidental overwrite.
    with open(args.output, "x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        file.flush()

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            for poll_number in range(1, args.count + 1):
                cycle_started = time.monotonic()
                poll_start_timestamp = utc_now()
                poll_id = f"{poll_number:06d}"
                results = {}

                futures = {
                    executor.submit(
                        read_sensor,
                        (index, sensor_url),
                        args.username,
                        password,
                        args.timeout,
                    ): index
                    for index, sensor_url in enumerate(sensor_urls)
                }

                for future in as_completed(futures):
                    index = futures[future]
                    try:
                        result_index, data = future.result()
                        results[result_index] = data
                    except Exception as exc:
                        # Defensive fallback if a worker itself raises unexpectedly.
                        sensor_url = sensor_urls[index]
                        results[index] = {
                            "sensor_id": sensor_url.rstrip("/").split("/")[-1],
                            "sensor_name": "", "reading": "", "units": "",
                            "health": "", "state": "", "lower_caution": "",
                            "lower_critical": "", "upper_caution": "",
                            "upper_critical": "", "request_status": "failure",
                            "sensor_url": sensor_url,
                            "error": f"WorkerError: {type(exc).__name__}: {exc}",
                        }

                poll_duration = time.monotonic() - cycle_started
                successful = sum(
                    1 for item in results.values()
                    if item["request_status"] == "success"
                )
                poll_status = "complete" if successful == len(sensor_urls) else "partial"
                timestamp = utc_now()

                # Write in the original Redfish collection order for reproducibility.
                for index in range(len(sensor_urls)):
                    data = results[index]
                    row = {
                        "timestamp": timestamp,
                        **data,
                        "poll_id": poll_id,
                        "poll_start_timestamp": poll_start_timestamp,
                        "poll_duration_seconds": f"{poll_duration:.6f}",
                        "poll_status": poll_status,
                    }
                    writer.writerow(row)

                file.flush()
                print(
                    f"Poll {poll_number}/{args.count}: "
                    f"{successful}/{len(sensor_urls)} successful; "
                    f"status={poll_status}; duration={poll_duration:.3f}s"
                )

                if poll_number < args.count:
                    remaining = args.interval - (time.monotonic() - cycle_started)
                    if remaining > 0:
                        time.sleep(remaining)

    print(f"Collection complete: {args.output}")


if __name__ == "__main__":
    main()
