# AST2600 Fan Tachometer Investigation

Date: 2026-11-21
Platform: QEMU 8.2.2, ASPEED AST2600 EVB
OpenBMC: v11.04

## 1. Objective

Investigate why fan tachometer telemetry consistently reports zero RPM
in the emulated AST2600 BMC.

## 2. Linux hwmon observations

Device:
- Name: aspeed_tach
- Device: /sys/devices/platform/ahb/1e610000.pwm-tach-controller
- Driver: aspeed-g6-pwm-tach
- Compatible: aspeed,ast2600-pwm-tach
- Device-tree node: /ahb/pwm-tach-controller@1e610000

Linux exposes fan1_input through fan16_input.
All 16 channels reported 0 RPM.

All corresponding fan*_div attributes reported 1.

## 3. Device-tree mapping

The controller has 16 child nodes: fan-0 through fan-15.

The tach-ch property values were inspected using BusyBox od -b.

Observed mappings:
- fan-0 -> channel 0
- fan-1 -> channel 1
- fan-2 -> channel 2
- fan-3 -> channel 3
- fan-4 -> channel 4
- fan-5 -> channel 5
- fan-6 -> channel 6
- fan-7 -> channel 7
- fan-8 -> channel 8
- fan-9 -> channel 9
- fan-10 -> channel 10
- fan-11 -> channel 11
- fan-12 -> channel 12
- fan-13 -> channel 13
- fan-14 -> channel 14
- fan-15 -> channel 15

The device-tree sequence is consistent with Linux hwmon attributes
fan1_input through fan16_input representing channels 0 through 15.

## 4. Entity Manager configuration

The AST2600 EVB Entity Manager configuration defines four fans:
- Fan 0: tach index 0, PWM 0
- Fan 1: tach index 1, PWM 1
- Fan 2: tach index 2, PWM 2
- Fan 3: tach index 3, PWM 3

Each fan is configured as AspeedFan.

The configured lower thresholds are:
- Lower non-critical: 480 RPM
- Lower critical: 360 RPM

The four configured fans correspond to the first four device-tree tach
channels.

## 5. QEMU source investigation

Inspected source tree:
qemu-ast2600-adc-experiment

QEMU version:
8.2.2

Findings:
- hw/arm/aspeed_ast2600.c defines ASPEED_DEV_PWM at 0x1E610000.
- No AST2600 PWM/tachometer device model was found in the inspected
  hw/ and include/ source directories.
- The shared ASPEED SoC structure declares pwm as UnimplementedDeviceState
  in include/hw/arm/aspeed_soc.h.
- AST1030 initializes and maps this PWM object as unimplemented in
  hw/arm/aspeed_ast10x0.c.
- No equivalent PWM object initialization or mapping was found in the
  inspected AST2600 initialization.
- hw/misc/npcm7xx_pwm.c implements PWM for NPCM7xx, not AST2600.

Therefore, the inspected QEMU 8.2.2 AST2600 source does not provide
a functional PWM/tachometer model.

## 6. Interpretation

The Linux driver exposes 16 tachometer channels, but all report zero RPM.
The QEMU source findings are consistent with the absence of functional
AST2600 tachometer emulation.

This does not prove that a physical tachometer would report zero RPM,
nor does it establish the behavior of every QEMU version or downstream
QEMU patch.

## 7. Data-quality decision

- Preserve raw fan telemetry.
- Mark fan RPM channels as unvalidated in the emulated environment.
- Do not use constant zero-RPM values as healthy normal training data.
- Exclude unvalidated fan RPM features from current ML training and
  evaluation.
- Retain the fan fault class in the project scope.
- Use documented synthetic data-layer fault injection for fan scenarios
  where appropriate.

## 8. Reproducibility

BMC commands used:
- Inspect /sys/class/hwmon/hwmon0
- Inspect /sys/class/hwmon/hwmon0/fan*_input
- Inspect /sys/class/hwmon/hwmon0/fan*_div
- Inspect /sys/class/hwmon/hwmon0/device/uevent
- Inspect /sys/firmware/devicetree/base/ahb/pwm-tach-controller@1e610000
- Decode tach-ch properties with BusyBox od -b

QEMU source commands used:
- grep -RniE '1e610000|pwm.tach|pwm_tach|pwm-tach|tach' hw include
- Inspect hw/arm/aspeed_ast2600.c
- Inspect hw/arm/aspeed_ast10x0.c
- Inspect hw/arm/aspeed_soc_common.c
- Inspect include/hw/arm/aspeed_soc.h
- Inspect references to s->pwm and TYPE_ASPEED_PWM

## 9. Future work

If fan tachometer anomaly detection is required with realistic dynamic
RPM behavior, investigate a QEMU AST2600 PWM/tachometer model or a
validated external telemetry source. Do not alter the running emulator
or its firmware image as part of this investigation.
