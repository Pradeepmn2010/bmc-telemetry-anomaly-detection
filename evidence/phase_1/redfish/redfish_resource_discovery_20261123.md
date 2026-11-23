# Redfish Resource Discovery — AST2600 Emulated BMC

- Date: 2026-11-23
- Platform: QEMU-emulated ASPEED AST2600
- OpenBMC release: v11.04
- Redfish endpoint: `https://127.0.0.1:2445`
- Authentication: HTTP Basic authentication
- TLS verification: Disabled for the local emulated BMC
- Result: PASS — 9/9 resource snapshots captured and validated

## 1. Objective

Inspect the Redfish resource hierarchy exposed by the emulated BMC to identify
available telemetry interfaces, collection limitations, and additional
resources relevant to server health monitoring.

The investigation was read-only. No BMC configuration, sensor configuration,
QEMU configuration, or fault-injection state was changed.

## 2. Resource discovery results

| Resource | HTTP | Observed result |
|---|---:|---|
| `/redfish/v1/Chassis` | 200 | Chassis collection accessible |
| `/redfish/v1/Managers` | 200 | Managers collection accessible |
| `/redfish/v1/Systems` | 200 | Systems collection accessible |
| `/redfish/v1/TelemetryService` | 200 | TelemetryService accessible |
| `/redfish/v1/Chassis/AST2600_EVB/EnvironmentMetrics` | 200 | Only Id and Name properties |
| `/redfish/v1/Chassis/AST2600_EVB/ThermalSubsystem` | 200 | Thermal subsystem enabled; links to Fans and ThermalMetrics |
| `/redfish/v1/Chassis/AST2600_EVB/ThermalSubsystem/ThermalMetrics` | 200 | One temperature reading |
| `/redfish/v1/Chassis/AST2600_EVB/ThermalSubsystem/Fans` | 200 | Fan collection contains zero members |
| `/redfish/v1/Chassis/AST2600_EVB/PowerSubsystem/PowerSupplies` | 200 | Power supply collection contains zero members |

## 3. Thermal telemetry findings

The ThermalSubsystem resource reports:

- Status Health: OK
- Status State: Enabled
- Fans resource: `/redfish/v1/Chassis/AST2600_EVB/ThermalSubsystem/Fans`
- ThermalMetrics resource: `/redfish/v1/Chassis/AST2600_EVB/ThermalSubsystem/ThermalMetrics`

ThermalMetrics exposes one entry in TemperatureReadingsCelsius:

- DataSourceUri: `/redfish/v1/Chassis/AST2600_EVB/Sensors/temperature_Ambient_Temp`
- Reading: 35.0 °C

The Fans collection returned HTTP 200 with Members@odata.count equal to zero.

This is consistent with the previously observed fan tachometer readings
of 0 RPM and PWM readings of 100%. Functional fan telemetry and fan fault
injection have not been validated in this QEMU environment.

## 4. Power subsystem findings

The PowerSubsystem resource returned HTTP 200 and reported:

- Id: PowerSubsystem
- Name: Power Subsystem
- Status Health: OK
- Status State: Enabled
- PowerSupplies link:
  `/redfish/v1/Chassis/AST2600_EVB/PowerSubsystem/PowerSupplies`

The PowerSupplies collection returned HTTP 200 with zero members.

Therefore, this collection currently provides no individual power-supply
resources for monitoring. This does not imply that voltage sensor readings
are unavailable through the separate Redfish Sensors collection.

## 5. EnvironmentMetrics finding

The EnvironmentMetrics endpoint returned HTTP 200 but exposed only:

- Id: EnvironmentMetrics
- Name: Chassis Environment Metrics

No temperature, voltage, or other metric values were exposed directly
in this resource response.

## 6. Implications for the anomaly-detection project

1. Continue using the Redfish Sensors collection as the primary telemetry
   source for the current anomaly-detection implementation.
2. ThermalMetrics provides an additional Redfish path to the ambient
   temperature reading.
3. Do not depend on the Fans collection for fan anomaly detection because
   it currently contains zero members.
4. Do not depend on the PowerSupplies collection for power-supply telemetry.
5. Continue investigating voltage telemetry through the existing ADC-backed
   sensor resources.
6. Treat missing collection members as an emulation/resource-exposure
   limitation, not as evidence that the corresponding physical hardware
   does not exist.
7. Do not interpret a successful HTTP response as proof that a resource
   contains usable telemetry.

## 7. Snapshot evidence

All nine inspected resources were captured on 2026-11-23.

Snapshot directory:

`evidence/phase_1/redfish/discovery_20261123/`

Files:

- `Chassis_collection.json`
- `Managers_collection.json`
- `Systems_collection.json`
- `TelemetryService.json`
- `EnvironmentMetrics.json`
- `ThermalSubsystem.json`
- `ThermalMetrics.json`
- `Fans_collection.json`
- `PowerSupplies_collection.json`
- `manifest.json`

Integrity validation:

- Manifest entries: 9
- Successful HTTP responses: 9
- Valid non-empty JSON objects: 9
- Failed snapshots: 0

SHA-256 hashes and capture timestamps are recorded in the manifest and
were independently calculated during validation.

## 8. Reproduction procedure

1. Start the existing AST2600 QEMU/OpenBMC test environment.
2. Confirm Redfish access at `https://127.0.0.1:2445`.
3. Authenticate using the local BMC credentials.
4. Issue GET requests to the nine endpoints listed in Section 2.
5. Save each successful JSON response separately.
6. Record endpoint, HTTP status, capture timestamp, and filename in a manifest.
7. Parse every saved file as JSON.
8. Verify that every snapshot is non-empty.
9. Calculate SHA-256 hashes for integrity verification.

The capture used Python requests with a persistent Session, HTTP Basic
authentication, JSON Accept headers, and TLS verification disabled for
the local emulated endpoint.

## 9. Limitations and scope

- This investigation covers the resources exposed by the current AST2600
  QEMU/OpenBMC configuration only.
- It does not establish that all Redfish resources supported by the broader
  Redfish specification are implemented.
- Zero-member collections may reflect the current emulation configuration.
- ThermalMetrics exposed one reading at the time of inspection; it is not
  established as a complete thermal telemetry interface.
- No fan or power-supply fault injection was performed in this investigation.
- This was a read-only resource discovery exercise, not an anomaly-detection
  performance evaluation.
- The live resource values may change with subsequent BMC configuration
  or software changes.

## 10. Conclusion

The resource discovery confirmed that the emulated BMC exposes accessible
Chassis, Managers, Systems, TelemetryService, ThermalSubsystem, and
PowerSubsystem resources.

ThermalMetrics exposes the ambient temperature reading, while the Fans
and PowerSupplies collections currently contain no members. EnvironmentMetrics
does not expose direct metric values.

For the current project implementation, the Redfish Sensors collection
remains the primary telemetry interface. The newly captured snapshots and
manifest provide reproducible evidence of the resource hierarchy observed
on 2026-11-23.
