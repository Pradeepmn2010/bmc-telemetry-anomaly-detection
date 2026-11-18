# Controlled Thermal Fault Injection and Recovery

- Date: 2026-11-18
- Platform: QEMU 8.2.2, ASPEED AST2600 OpenBMC
- Sensor: TMP105 ambient temperature
- Injection method: QEMU QOM temperature property
- Collection interval: 2 seconds
- Polls per phase: 30

## Experimental results

### NORMAL_REFERENCE
- Dataset: `data/raw/thermal_experiment_20261118.csv`
- Total sensor records: 360
- Temperature samples: 30
- Temperature readings: [25.0]
- Health: {'OK': 30}
- State: {'Enabled': 30}
- SHA256: `26d37ff5a31aaea4539d3fde2b5e70312ec91f08cef8a108ecce03fd21699bdf`

### THERMAL_FAULT_60C
- Dataset: `data/raw/thermal_fault_60c_20261118.csv`
- Total sensor records: 360
- Temperature samples: 30
- Temperature readings: [60.0]
- Health: {'Critical': 30}
- State: {'Enabled': 30}
- SHA256: `b86dedc260b6fa2314003f1f091656b4b194e9db7acf3b730f14bb31313c87bd`

### RECOVERY_25C
- Dataset: `data/raw/thermal_recovery_25c_20261118.csv`
- Total sensor records: 360
- Temperature samples: 30
- Temperature readings: [25.0]
- Health: {'OK': 30}
- State: {'Enabled': 30}
- SHA256: `e62d1048c417726475c8631a277fea81e28f87b97637f122b9e347d92c1e8cde`

## Conclusion

The emulated temperature sensor reported 25°C with Health=OK during the normal-reference phase, 60°C with Health=Critical during thermal fault injection, and 25°C with Health=OK during recovery.

This validates the temperature fault injection and recovery path in the QEMU-emulated AST2600 OpenBMC environment. It does not represent a physical hardware fault or establish a complete healthy baseline for all BMC sensors.
