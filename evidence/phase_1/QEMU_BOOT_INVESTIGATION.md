# QEMU OpenBMC Boot Investigation

## 1. Environment

| Parameter | Value |
|---|---|
| Emulator | QEMU 8.2.2 |
| Machine | AST2600 EVB |
| Firmware | ASPEED OpenBMC v11.04 |
| Firmware target | ast2600-default |
| Flash image | ast2600-default.static.mtd |
| Flash image size | 64 MiB |
| RAM | 1024 MiB |
| Host SSH forwarding | 127.0.0.1:2222 |
| Host HTTPS forwarding | 127.0.0.1:2443 |

## 2. Objective

Investigate whether the ASPEED OpenBMC firmware image can boot
successfully under QEMU and identify hardware-emulation or firmware
compatibility issues that prevent normal operation.

## 3. Boot observations

The captured logs show that:

- QEMU starts the AST2600 virtual machine.
- U-Boot SPL and U-Boot output are present in the captured traces.
- U-Boot reports detecting a 64 MiB SPI flash device in one test.
- Linux kernel startup messages are present.
- Linux does not complete a successful boot in the examined traces.

The presence of U-Boot and Linux messages does not establish that
the complete OpenBMC operating system has booted successfully.

## 4. Errors observed

### 4.1 SPI NOR flash

The logs contain errors including:

- BFPT parsing failure.
- SPI NOR probe failure with error -22.
- Unrecognized JEDEC ID values, including all-zero bytes in one test.
- SPI flash device detection differs across the tested configurations.

These observations suggest that SPI NOR identification or emulation
compatibility requires further investigation.

### 4.2 I3C controllers

The logs contain I3C controller recovery or probe failures,
including error -110.

The cause and impact on the boot sequence have not yet been
established.

### 4.3 ADT7475

An error was observed while configuring the ADT7475 attenuator
bypass.

Further investigation is required to determine whether this is
related to QEMU device emulation or firmware configuration.

### 4.4 MMC

The logs report that mmc0 failed to initialize a non-removable card.

The dependency of the boot process on this device is not yet known.

### 4.5 Root filesystem and kernel panic

The captured traces report MTD root filesystem mount failures,
including failures involving /dev/mtdblock, followed by a fatal
kernel panic.

This is the clearest observed blocker to successful Linux boot.

## 5. Test evidence

The following raw logs are retained locally:

| Log file | Purpose |
|---|---|
| qemu-first-boot.log | Initial boot trace |
| qemu-flash-model-test.log | Flash model test |
| qemu-w25q512jv-test.log | W25Q512JV flash model test |
| qemu-xip-test.log | Execute-in-place configuration test |
| qemu-three-flash-test.log | Additional flash configuration test |
| qemu-console.log | QEMU console trace |
| qemu-clean-console.log | Cleaned console trace |

These are raw diagnostic captures. Preserve them unchanged.

## 6. Current assessment

The current evidence establishes that the emulator starts and
produces bootloader and Linux kernel output.

It does not establish a successful complete OpenBMC boot.

The SPI NOR probe errors and MTD root filesystem mount failures
are priority investigation items. I3C, ADT7475 and MMC errors
are additional observations whose relationship to the boot failure
remains unverified.

No conclusion is made that a particular flash model or QEMU
configuration resolves the problem.

## 7. Next investigation steps

1. Confirm the exact SPI NOR model and JEDEC ID expected by the
   firmware device tree.
2. Inspect the firmware device tree for SPI controller, flash
   partitions and MTD configuration.
3. Compare the firmware's expected flash layout with the actual
   64 MiB image layout.
4. Investigate why BFPT parsing and SPI NOR probing fail.
5. Determine why the MTD root filesystem cannot mount.
6. Examine I3C, ADT7475 and MMC errors separately.
7. Change one QEMU parameter at a time and preserve each test log.
8. Confirm successful Linux and OpenBMC service startup before
   declaring the platform operational.

## 8. Reproducibility and limitations

- QEMU version and firmware details must be recorded with each test.
- Preserve the original firmware image and its SHA-256 checksum.
- Do not overwrite the pristine flash image.
- Preserve raw console logs separately from summaries.
- Do not treat a U-Boot prompt or kernel startup message as proof
  of successful OpenBMC boot.
- All observations are from emulation and do not establish
  physical AST2600 hardware behaviour.

## 9. Phase 1 status

QEMU-based OpenBMC emulation is partially operational.

SSH and HTTPS forwarding were previously confirmed available,
and Redfish ServiceRoot returned a response. However, the captured
boot traces contain failures that still require investigation.

Phase 1 is not complete until the telemetry source and sensor
validity are sufficiently established for a documented baseline.

## 10. Firmware integrity

The firmware archive and flash image were checksummed using SHA-256.

| Artifact | SHA-256 |
|---|---|
| ast2600-default-obmc.tar.gz | `f0603e7255b2b3c720f50928b9ea20fc2edc2d4c5eb0e3f119e4489e91c59820` |
| ast2600-default.static.mtd | `9df7beea2097df647bd60054474c38eff3fa093e8ba8dfd5f2a4321e417e010b` |

The checksum records are preserved in
`evidence/phase_1/firmware-sha256.txt`.

The firmware archive and flash image are retained locally and are
excluded from GitHub because of their size.
