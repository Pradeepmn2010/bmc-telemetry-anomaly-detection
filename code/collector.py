#!/usr/bin/env python3
"""
collector.py  -  Phase 2: Telemetry collection
Polls the emulated BMC's Redfish sensors at a fixed interval and appends
each reading, with a timestamp, to data/normal.csv.

Run:  python3 collector.py --url https://localhost:2443 --interval 5 --out data/normal.csv
Stop: Ctrl-C  (the CSV keeps everything collected so far)
"""
import argparse
import csv
import getpass
import os
import sys
import time
from datetime import datetime, timezone

import requests
import urllib3

# The emulated BMC uses a self-signed certificate; silence the warning.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER = os.environ.get("BMC_USERNAME", "root")
PASSWORD = None  # Supplied securely at runtime.


def discover_sensor_collection(base_url):
    """Find the Sensors collection URL by walking Redfish: root -> Chassis -> Sensors."""
    s = requests.Session()
    s.auth = (USER, PASSWORD)
    s.verify = False

    chassis = s.get(f"{base_url}/redfish/v1/Chassis", timeout=10).json()
    members = chassis.get("Members", [])
    if not members:
        raise RuntimeError("No chassis found on the BMC - is it fully booted?")
    chassis_url = base_url + members[0]["@odata.id"]
    chassis_obj = s.get(chassis_url, timeout=10).json()
    sensors_ref = chassis_obj.get("Sensors", {}).get("@odata.id")
    if not sensors_ref:
        raise RuntimeError("This chassis exposes no Sensors collection.")
    return base_url + sensors_ref


def read_all_sensors(base_url, sensors_url):
    """Return a dict {sensor_name: reading} for the current moment."""
    s = requests.Session()
    s.auth = (USER, PASSWORD)
    s.verify = False

    coll = s.get(sensors_url, timeout=10).json()
    readings = {}
    for m in coll.get("Members", []):
        sref = base_url + m["@odata.id"]
        try:
            obj = s.get(sref, timeout=10).json()
            name = obj.get("Name")
            value = obj.get("Reading")
            if name is not None and value is not None:
                readings[name] = value
        except Exception as e:
            print(f"  [warn] could not read {sref}: {e}", file=sys.stderr)
    return readings


def main():
    global PASSWORD
    PASSWORD = os.environ.get("BMC_PASSWORD") or getpass.getpass("BMC password: ")

    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://localhost:2443",
                    help="Base URL of the BMC Redfish service")
    ap.add_argument("--interval", type=float, default=5.0,
                    help="Seconds between polls")
    ap.add_argument("--out", default="data/normal.csv", help="Output CSV path")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    print(f"Discovering sensors on {args.url} ...")
    sensors_url = discover_sensor_collection(args.url)
    first = read_all_sensors(args.url, sensors_url)
    if not first:
        print("No sensors returned a reading. Check the BMC is booted.", file=sys.stderr)
        sys.exit(1)

    columns = ["timestamp"] + sorted(first.keys())
    print(f"Logging {len(columns)-1} sensors: {', '.join(columns[1:])}")
    print(f"Writing to {args.out}  (Ctrl-C to stop)")

    new_file = not os.path.exists(args.out) or os.path.getsize(args.out) == 0
    with open(args.out, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if new_file:
            writer.writeheader()

        count = 0
        try:
            while True:
                t0 = time.time()
                readings = read_all_sensors(args.url, sensors_url)
                row = {"timestamp": datetime.now(timezone.utc).isoformat()}
                for col in columns[1:]:
                    row[col] = readings.get(col, "")   # blank if missing this poll
                writer.writerow(row)
                f.flush()                              # keep data even if killed
                count += 1
                if count % 10 == 0:
                    print(f"  logged {count} rows...")
                # keep a steady cadence
                sleep = args.interval - (time.time() - t0)
                if sleep > 0:
                    time.sleep(sleep)
        except KeyboardInterrupt:
            print(f"\nStopped. {count} rows written to {args.out}.")


if __name__ == "__main__":
    main()
