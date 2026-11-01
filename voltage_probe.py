import getpass
import time
from datetime import datetime, timezone

import requests
import urllib3

urllib3.disable_warnings()

base = "https://127.0.0.1:2443"
user = input("BMC username [root]: ").strip() or "root"
password = getpass.getpass("BMC password: ")

s = requests.Session()
s.auth = (user, password)
s.verify = False
s.headers["Accept"] = "application/json"

sensor_ids = ("voltage_ADC0_12V", "voltage_ADC8_12V")

for sample in range(1, 36):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for sensor_id in sensor_ids:
        path = f"/redfish/v1/Chassis/AST2600_EVB/Sensors/{sensor_id}"
        try:
            response = s.get(base + path, timeout=5)
            response.raise_for_status()
            data = response.json()
            print(
                timestamp,
                sensor_id,
                "Reading =", data.get("Reading"),
                "Health =", data.get("Status", {}).get("Health"),
                flush=True,
            )
        except requests.RequestException as exc:
            print(timestamp, sensor_id, "ERROR:", exc, flush=True)

    time.sleep(1)
