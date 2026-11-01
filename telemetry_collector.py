import csv
import getpass
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://127.0.0.1:2443"
SENSORS = "/redfish/v1/Chassis/AST2600_EVB/Sensors"
OUTPUT = Path("data/baseline_telemetry.csv")
INTERVAL = 5
DURATION = 300

username = input("BMC username [root]: ").strip() or "root"
password = getpass.getpass("BMC password: ")

session = requests.Session()
session.auth = (username, password)
session.verify = False
session.headers["Accept"] = "application/json"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

def fetch_sensors():
    response = session.get(BASE + SENSORS, timeout=10)
    response.raise_for_status()
    collection = response.json()

    records = []
    for member in collection.get("Members", []):
        uri = member.get("@odata.id")
        if not uri:
            continue

        r = session.get(BASE + uri, timeout=10)
        r.raise_for_status()
        sensor = r.json()

        records.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sensor_id": sensor.get("Id", ""),
            "name": sensor.get("Name", ""),
            "reading": sensor.get("Reading"),
            "units": sensor.get("ReadingUnits", ""),
            "health": sensor.get("Status", {}).get("Health", ""),
            "state": sensor.get("Status", {}).get("State", ""),
        })

    return records

print(f"Collecting for {DURATION // 60} minutes, every {INTERVAL} seconds.")
print(f"Output: {OUTPUT}")
print("Press Ctrl+C to stop early.")

start = time.monotonic()
samples = 0

try:
    with OUTPUT.open("w", newline="") as file:
        fields = [
            "timestamp", "sensor_id", "name",
            "reading", "units", "health", "state"
        ]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        while time.monotonic() - start < DURATION:
            cycle_start = time.monotonic()
            try:
                rows = fetch_sensors()
                writer.writerows(rows)
                file.flush()
                samples += 1
                print(
                    f"Sample {samples}: {len(rows)} sensors, "
                    f"{datetime.now().strftime('%H:%M:%S')}"
                )
            except (requests.RequestException, ValueError) as exc:
                print("Collection error:", exc)

            remaining = INTERVAL - (time.monotonic() - cycle_start)
            if remaining > 0:
                time.sleep(min(remaining, max(0, DURATION - (time.monotonic() - start))))

except KeyboardInterrupt:
    print("\nCollection stopped by user.")

print(f"Finished. Samples collected: {samples}")
print(f"CSV saved to {OUTPUT}")
