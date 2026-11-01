import getpass
import json
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

for sensor_id in ("voltage_ADC0_12V", "voltage_ADC8_12V"):
    path = f"/redfish/v1/Chassis/AST2600_EVB/Sensors/{sensor_id}"

    print(f"\n{'=' * 60}\n{sensor_id}")
    try:
        response = s.get(base + path, timeout=10)
        print("HTTP:", response.status_code)
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
    except requests.RequestException as exc:
        print("Request error:", exc)
