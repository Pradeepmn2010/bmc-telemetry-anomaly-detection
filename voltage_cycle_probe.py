import csv
import getpass
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings()

BASE = "https://127.0.0.1:2443"
SENSORS = ("voltage_ADC0_12V", "voltage_ADC8_12V")
OUTPUT = Path("data/voltage_cycle_probe.csv")

user = input("BMC username [root]: ").strip() or "root"
password = getpass.getpass("BMC password: ")

session = requests.Session()
session.auth = (user, password)
session.verify = False
session.headers["Accept"] = "application/json"

# Verify authentication before starting the collection.
test = session.get(
    BASE + "/redfish/v1/Chassis/AST2600_EVB/Sensors",
    timeout=10,
)
print("Authentication check:", test.status_code)
test.raise_for_status()

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="") as f:
    fields = ["timestamp", "sensor_id", "reading", "health"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    start = time.monotonic()
    sample = 0

    while time.monotonic() - start < 140:
        sample += 1
        cycle_start = time.monotonic()

        for sensor_id in SENSORS:
            path = (
                "/redfish/v1/Chassis/AST2600_EVB/Sensors/"
                + sensor_id
            )
            r = session.get(BASE + path, timeout=10)
            r.raise_for_status()
            data = r.json()

            row = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sensor_id": sensor_id,
                "reading": data.get("Reading"),
                "health": data.get("Status", {}).get("Health"),
            }
            writer.writerow(row)
            f.flush()

            print(
                f"Sample {sample}: {sensor_id} = "
                f"{row['reading']} V, {row['health']}",
                flush=True,
            )

        remaining = 2 - (time.monotonic() - cycle_start)
        if remaining > 0:
            time.sleep(remaining)

print("Saved:", OUTPUT)
