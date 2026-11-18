#!/usr/bin/env python3
import argparse
import csv
import getpass
import os
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FIELDS = [
    "timestamp", "sensor_id", "sensor_name", "reading", "units",
    "health", "state", "lower_caution", "lower_critical",
    "upper_caution", "upper_critical",
]

def get_json(session, url):
    response = session.get(url, timeout=15, verify=False)
    response.raise_for_status()
    return response.json()

def find_sensor_collection(session, base_url):
    chassis = get_json(session, urljoin(base_url, "/redfish/v1/Chassis"))
    members = chassis.get("Members", [])
    if not members:
        raise RuntimeError("No Redfish chassis found")

    chassis_url = urljoin(base_url, members[0]["@odata.id"])
    chassis_data = get_json(session, chassis_url)
    sensors_link = chassis_data.get("Sensors", {}).get("@odata.id")
    if not sensors_link:
        raise RuntimeError("Chassis does not expose a Sensors collection")

    return urljoin(base_url, sensors_link)

def main():
    parser = argparse.ArgumentParser(description="Collect Redfish sensor telemetry")
    parser.add_argument("--url", default="https://127.0.0.1:2445")
    parser.add_argument("--username", default="root")
    parser.add_argument("--output", default="data/raw/redfish_telemetry.csv")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--count", type=int, default=60)
    args = parser.parse_args()

    if args.interval <= 0 or args.count <= 0:
        parser.error("--interval and --count must be positive")

    if os.path.exists(args.output):
        parser.error(f"Output already exists; choose another path: {args.output}")

    password = getpass.getpass("BMC password: ")
    session = requests.Session()
    session.auth = (args.username, password)
    session.verify = False
    session.headers.update({"Accept": "application/json"})

    collection_url = find_sensor_collection(session, args.url.rstrip("/") + "/")
    collection = get_json(session, collection_url)
    sensor_urls = [
        urljoin(args.url.rstrip("/") + "/", member["@odata.id"].lstrip("/"))
        for member in collection.get("Members", [])
    ]

    if not sensor_urls:
        raise RuntimeError("No sensors found in Redfish collection")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    print(f"Found {len(sensor_urls)} sensors. Collecting {args.count} polls.")

    with open(args.output, "x", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()

        for poll in range(args.count):
            timestamp = datetime.now(timezone.utc).isoformat()
            rows_written = 0

            for sensor_url in sensor_urls:
                try:
                    sensor = get_json(session, sensor_url)
                    status = sensor.get("Status") or {}
                    thresholds = sensor.get("Thresholds") or {}

                    def threshold_value(name):
                        return (thresholds.get(name) or {}).get("Reading", "")

                    row = {
                        "timestamp": timestamp,
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
                    }
                    writer.writerow(row)
                    rows_written += 1
                except requests.RequestException as exc:
                    print(f"Sensor read failed ({sensor_url}): {exc}")

            file.flush()
            print(f"Poll {poll + 1}/{args.count}: wrote {rows_written}/{len(sensor_urls)} sensor records")

            if poll + 1 < args.count:
                time.sleep(args.interval)

    print(f"Collection complete: {args.output}")

if __name__ == "__main__":
    main()
