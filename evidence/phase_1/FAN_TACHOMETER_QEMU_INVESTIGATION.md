# AST2600 Fan Tachometer Investigation — QEMU 8.2.2

## 1. Objective

Investigate why the four OpenBMC fan tachometer sensors report zero RPM
in the AST2600 QEMU environment, despite the Linux tachometer driver
being bound and PWM sensors reporting 100%.

The investigation uses read-only inspection of the running BMC,
Linux sysfs, device tree, pinctrl, D-Bus, and QEMU 8.2.2 source code.

## 2. Test Environment

- Emulator: QEMU 8.2.2
- Machine: AST2600 EVB
- Firmware: ASPEED OpenBMC v11.04
- Kernel: 6.18.50-v00.08.04-g76457d3afe2b
- Architecture: ARMv7
- Project environment: Ubuntu 24.04.4 LTS under WSL2
- QEMU source directory: qemu-8.2.2+ds/

The running QEMU instance was not restarted during this investigation.

## 3. Linux Tachometer Driver

The tachometer hardware-monitor device was identified as:

- hwmon device: hwmon0
- Device name: aspeed_tach
- Device-tree compatible: aspeed,ast2600-pwm-tach
- Device-tree controller address: 0x1e610000
- Platform driver: aspeed-g6-pwm-tach
- Platform device: 1e610000.pwm-tach-controller

The driver was bound to the platform device.

The device-tree controller node was enabled (status = okay).
Sixteen tachometer child nodes were present.

The first four tachometer channels were configured as:

| Fan node | tach-ch |
|---|---:|
| fan-0 | 0 |
| fan-1 | 1 |
| fan-2 | 2 |
| fan-3 | 3 |

## 4. Tachometer Measurements

The Linux hwmon device exposed fan1_input through fan16_input.

All sixteen readings were zero RPM during the inspected snapshots.

The first four channels were also checked repeatedly. No nonzero
tachometer readings were observed.

All tachometer divider values were 1.

## 5. PWM Measurements

Fifteen pwm-fan devices were identified.

The first four PWM devices corresponded to:

- pwm-fan0
- pwm-fan1
- pwm-fan2
- pwm-fan3

All fifteen PWM devices reported:

- pwm1 = 255
- pwm1_enable = 1

The first four OpenBMC PWM sensors reported 100%.

A PWM value of 255 represents the maximum value of the observed
8-bit PWM range. This does not establish that a physical fan is
rotating.

## 6. OpenBMC D-Bus Observations

The FanSensor service exposed four fan tachometer sensors:

- Fan_0
- Fan_1
- Fan_2
- Fan_3

For all four sensors:

- Sensor.Value.Value = 0
- Available = true
- Functional = true
- WarningAlarmLow = true
- CriticalAlarmLow = true
- WarningLow = 480 RPM
- CriticalLow = 360 RPM

The corresponding PWM sensors reported 100%.

These observations show that OpenBMC exposes the configured sensors
and asserts low-speed alarms at zero RPM.

## 7. Pinmux and Clock Observations

The AST2600 tachometer controller device-tree node was enabled.

The pinctrl debug information showed TACH0 through TACH15 assigned
to the pwm-tach-controller device.

The AHB clock was observed as enabled in the clock summary, with
a reported frequency of 200 MHz.

The tachometer platform driver was bound.

These observations establish that the Linux configuration and
driver setup are present. They do not prove that QEMU generates
tachometer input pulses.

## 8. QEMU 8.2.2 Source Investigation

The QEMU source package was downloaded for inspection without
installing or upgrading QEMU.

### 8.1 Shared ASPEED SoC structure

File:
include/hw/arm/aspeed_soc.h

Line 88 declares:

    UnimplementedDeviceState pwm;

This identifies the shared ASPEED PWM device object as an
unimplemented-device type.

### 8.2 Unimplemented MMIO mapping helper

File:
hw/arm/aspeed_soc_common.c

The function aspeed_mmio_map_unimplemented() sets the device name
and size, realizes the device, and maps its MMIO region using
memory_region_add_subregion_overlap().

This confirms how QEMU maps devices explicitly passed to this helper.

### 8.3 AST2600 memory map

File:
hw/arm/aspeed_ast2600.c

The AST2600 memory map declares:

    [ASPEED_DEV_PWM] = 0x1E610000,

The AST2600 interrupt map declares:

    [ASPEED_DEV_PWM] = 44,

The AST2600 source file contains no PWM-specific initialization
or mapping reference beyond these memory-map and interrupt-map
declarations.

### 8.4 AST10x0 comparison

File:
hw/arm/aspeed_ast10x0.c

The AST10x0 implementation explicitly initializes the PWM object
as TYPE_UNIMPLEMENTED_DEVICE and maps it using
aspeed_mmio_map_unimplemented().

This is evidence for AST10x0 behavior only. It must not be treated
as proof that AST2600 uses the same mapping path.

### 8.5 Source investigation conclusion

The QEMU 8.2.2 source represents the shared ASPEED PWM object as
unimplemented. The AST2600 memory map declares its PWM address,
but the inspected AST2600 realization function does not show
a corresponding functional PWM initialization or explicit
unimplemented mapping.

Therefore, the source inspection strongly suggests incomplete
AST2600 PWM/tachometer emulation.

The exact runtime behavior of MMIO accesses at 0x1E610000 has
not yet been independently verified.

## 9. Root-Cause Assessment

Most likely explanation:

The QEMU AST2600 model does not provide the PWM/tachometer hardware
behavior needed to generate tachometer pulses for the Linux driver.

Evidence supporting this hypothesis:

1. All inspected tachometer inputs report zero RPM.
2. PWM devices report maximum duty values.
3. The Linux tachometer driver is bound.
4. The device tree enables the tachometer controller.
5. Tachometer pins are assigned through pinctrl.
6. The QEMU source declares the shared ASPEED PWM object as
   UnimplementedDeviceState.
7. No AST2600 PWM initialization was found in the inspected
   AST2600 realization source.

This is a strong hypothesis, not a fully proven runtime root cause.

Alternative explanations such as missing signal connections,
board-specific configuration, or other emulation limitations
have not been completely excluded.

## 10. Limitations

- No physical AST2600 board was used for comparison.
- No tachometer pulse generator was connected.
- QEMU MMIO register read/write behavior at 0x1E610000 has not
  yet been directly traced.
- The investigation does not establish actual physical fan behavior.
- Source conclusions apply to the inspected QEMU 8.2.2 package.
- The AST10x0 implementation is not proof of AST2600 runtime behavior.

## 11. Reproduction Procedure

### Linux/BMC checks

1. Inspect hardware-monitor devices:

       for h in /sys/class/hwmon/hwmon*; do
           printf '%s ' "$h"
           cat "$h/name" 2>/dev/null
       done

2. Inspect tachometer values:

       for f in /sys/class/hwmon/hwmon0/fan*_input; do
           [ -f "$f" ] && printf '%s=' "$f" && cat "$f"
       done

3. Inspect PWM values:

       for f in /sys/class/hwmon/hwmon*/pwm1; do
           [ -f "$f" ] && printf '%s=' "$f" && cat "$f"
       done

4. Inspect tachometer driver binding:

       readlink -f /sys/bus/platform/devices/1e610000.pwm-tach-controller/driver

5. Inspect device-tree status and compatibility:

       tr -d '\0' < /sys/firmware/devicetree/base/ahb/pwm-tach-controller@1e610000/status
       tr '\0' '\n' < /sys/firmware/devicetree/base/ahb/pwm-tach-controller@1e610000/compatible

### QEMU source checks

From the directory containing qemu-8.2.2+ds:

1. Inspect the shared PWM object declaration:

       grep -n -C 4 'UnimplementedDeviceState pwm' include/hw/arm/aspeed_soc.h

2. Inspect the unimplemented mapping helper:

       sed -n '106,115p' hw/arm/aspeed_soc_common.c

3. Inspect AST2600 PWM address declaration:

       grep -n -C 2 'ASPEED_DEV_PWM' hw/arm/aspeed_ast2600.c

4. Search AST2600 PWM references:

       grep -n 'pwm' hw/arm/aspeed_ast2600.c

## 12. Next Steps

1. Verify AST2600 MMIO behavior at 0x1E610000 without changing
   the running emulator.
2. Inspect the relevant QEMU memory-region and unimplemented-device
   implementation.
3. Investigate the ambient temperature sensor.
4. Investigate battery ADC channel configuration and validity.
5. Revisit ADC scaling and low-side alarm behavior.
6. Collect a new baseline only after sensor validity is established.
7. Keep zero-RPM readings classified as an emulation limitation
   candidate, not as a confirmed physical fan fault.

## 13. Project Data Integrity

The original telemetry captures must remain unchanged.

The QEMU source inspection does not modify the firmware image,
flash image, running BMC, or emulator process.

Large firmware images, source archives, and virtual environments
must remain excluded from GitHub.

No Git commit or push is authorized by this report's creation.
