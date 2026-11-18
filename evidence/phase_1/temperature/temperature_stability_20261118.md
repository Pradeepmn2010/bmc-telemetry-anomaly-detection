# Temperature Steady-State Stability Audit

- Date: 2026-11-18
- Test condition: QEMU AST2600 OpenBMC, ambient temperature configured at 25°C
- Collection dataset: `data/raw/temperature_stability_20261118.csv`
- Total CSV records: 720
- Temperature samples: 60
- First timestamp: 2026-11-18 17:02:05.957770+00:00
- Last timestamp: 2026-11-18 17:07:32.817225+00:00
- Health: {'OK': 60}
- State: {'Enabled': 60}
- Minimum: 25.0 °C
- Maximum: 25.0 °C
- Mean: 25.0000 °C
- Standard deviation (sample): 0.000000 °C
- Unique readings: 1
- Missing readings: 0
- Dataset SHA256: `38ef573df020187abe6111a0f2c134ff15fb60619743fda46f0eaa359a225683`

## Result

The ambient temperature sensor reported 25.0°C in all 60 samples.
All samples reported Health=OK and State=Enabled.

## Interpretation and limitations

This experiment demonstrates steady-state stability of the emulated temperature
telemetry under the tested condition. It does not establish a representative
dynamic healthy baseline. The zero-variance readings must not be treated as
proof of real-world sensor variability or sufficient ML training data.

This dataset is classified as a steady-state stability experiment, not an
approved complete healthy ML baseline.
