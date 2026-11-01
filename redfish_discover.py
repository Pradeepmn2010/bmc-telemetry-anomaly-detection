
import getpass
import json
import requests
import urllib3

urllib3.disable_warnings()
BASE = "https://127.0.0.1:2443"
CHASSIS = "/redfish/v1/Chassis/AST2600_EVB"

user = input("BMC username [root]: ").strip() or "root"
password = getpass.getpass("BMC password: ")

s = requests.Session()
s.auth = (user, password)
s.verify = False
s.headers["Accept"] = "application/json"

def get(path):
    r = s.get(BASE + path, timeout=10)
    print(f"HTTP {r.status_code}: {path}")
    r.raise_for_status()
    return r.json()

print("\n=== Sensor collection ===")
try:
    collection = get(CHASSIS + "/Sensors")
    members = collection.get("Members", [])
    print("Sensor count:", len(members))

    for member in members:
        uri = member.get("@odata.id")
        if not uri:
            continue
        try:
            d = get(uri)
            print(json.dumps({
                "Id": d.get("Id"),
                "Name": d.get("Name"),
                "Reading": d.get("Reading"),
                "ReadingType": d.get("ReadingType"),
                "ReadingUnits": d.get("ReadingUnits"),
                "Status": d.get("Status"),
                "PhysicalContext": d.get("PhysicalContext"),
            }, indent=2))
        except requests.RequestException as e:
            print("Sensor error:", uri, e)
except requests.RequestException as e:
    print("Sensor collection error:", e)

for name in ("ThermalSubsystem", "PowerSubsystem"):
    print(f"\n=== {name} ===")
    try:
        print(json.dumps(get(CHASSIS + "/" + name), indent=2)[:6000])
    except requests.RequestException as e:
        print(name, "error:", e)
