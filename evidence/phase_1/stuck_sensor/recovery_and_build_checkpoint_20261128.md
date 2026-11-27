# QEMU Recovery and Independent Build Checkpoint

## 1. Date and project context
- Date: 2026-11-28
- Project: ML-Based Anomaly Detection on Emulated BMC for Server Health Monitoring
- Platform: WSL2 Ubuntu 24.04.4
- QEMU source version: 8.2.2
- Target machine: ASPEED AST2600 EVB
- OpenBMC image: v11.04
- Investigation: Emulator-level TMP105 stuck-sensor fault

## 2. Existing BMC session — preserved
- Original QEMU PID: 9633
- Last verified process status: Sl+
- Last observed elapsed runtime: 1 day, 12 hours, 55 minutes
- The existing BMC session was not stopped or restarted during recovery or independent compilation.
- Original launch command is preserved in:
  recovered_qemu_launch_command.txt
- Running process command line uses:
  testbed/images/experiments/ast2600-telemetry-validation-20261117.mtd
- SSH host forwarding: 127.0.0.1:2225 to guest port 22
- HTTPS host forwarding: 127.0.0.1:2445 to guest port 443
- ADC stable sampling enabled.
- ADC engine 0 data0 configured as 0x0014000A.

Important: The running process may still reference its original unlinked executable inode through /proc/9633/exe. Restoring a file at the same pathname does not change the executable inode already held by the running process.

## 3. Original executable recovery
Recovered executable:
- Path: evidence/phase_1/stuck_sensor/qemu-system-arm-recovered
- Size: approximately 83 MB
- Format: ELF 64-bit x86-64 PIE, dynamically linked, with debug information
- QEMU version: 8.2.2
- Build ID: b26449c40d053bab939eb6117bc8b97f47bc57cd
- SHA-256: ee380b1a52516acde2d9fdf04c2196d556fdeff11ab1a08c46591ce9e2940139

A copy was restored to:
qemu-ast2600-adc-experiment/build/qemu-system-arm

The restored file was verified to have the same SHA-256 as the recovered executable.

This restores the executable file at the original path. It does not restore the deleted original Meson/Ninja build metadata.

## 4. Recovery incident and investigation
The original build directory lost its Meson/Ninja metadata and executable during the recovery incident. The configure log in the original build directory records a configure invocation with --help from the source tree.

The likely cause is that running the QEMU configure script with --help from the source root created or reinitialized the default build directory. This is the best-supported explanation from the observed timeline and remaining config.log; the exact filesystem deletion mechanism was not independently established.

The original executable was recovered from the still-running QEMU process before further build work.

The original build directory was not used for the new compilation.

## 5. Independent QEMU build
A separate build directory was created:
qemu-ast2600-adc-experiment/build-stuck-sensor-system

Configure was run from outside the project's parent Python virtual environment so the QEMU build could use the system Meson installation.

Configure command:
../configure --target-list=arm-softmmu --disable-install-blobs -Dgtk=disabled -Dsdl=disabled -Dvnc=disabled -Dspice=disabled -Dcurl=disabled -Dslirp=enabled -Ddocs=disabled -Dplugins=true

Build command:
ninja -j2 qemu-system-arm

Build result:
- Completed successfully: 1901/1901 steps
- Parallel jobs: 2
- New executable: build-stuck-sensor-system/qemu-system-arm
- QEMU version: 8.2.2
- AST2600 machine listing: ast2600-evb Aspeed AST2600 EVB (Cortex-A7)
- File format: ELF 64-bit LSB PIE executable, x86-64, dynamically linked, with debug_info, not stripped
- Build ID: 6dfc76383f267f91ae6407b09992fa5acef751b2
- SHA-256: ab3d017c02c3c66b5b3a0a48edd0a7c0f26f489c2bec2c2a748c9080d7a51ce6

The new executable is distinct from the recovered original executable.

## 6. Configure observations
- System Python: /usr/bin/python3, version 3.12.3
- System Meson: 1.3.2
- Ninja: 1.11.1
- Target: arm-softmmu
- Main QEMU plugin support was enabled in the generated configuration.
- ASPEED SoC configuration was present.
- Documentation dependencies were unavailable offline; documentation build was disabled.
- Configure printed an optional TCG test configuration path warning. The main QEMU build nevertheless completed successfully.
- No claim is made that optional TCG test configuration was validated.

## 7. Verification commands and results
Run from build-stuck-sensor-system:

1. ./qemu-system-arm --version
   Result: QEMU emulator version 8.2.2

2. ./qemu-system-arm -machine help | grep -i ast2600
   Result: ast2600-evb Aspeed AST2600 EVB (Cortex-A7)

3. sha256sum ./qemu-system-arm
   Result: ab3d017c02c3c66b5b3a0a48edd0a7c0f26f489c2bec2c2a748c9080d7a51ce6

4. file ./qemu-system-arm
   Result: valid x86-64 ELF PIE executable with debug_info

5. ps -p 9633 -o pid,stat,etime,comm
   Result: PID 9633 remained alive, status Sl+, elapsed 1-12:55:17 at the time of verification.

The new executable has not been launched. The existing BMC session remains the active guest session.

## 8. Stuck-sensor experiment status
The preliminary investigation is documented separately in:
preliminary_investigation_20261127.md

That investigation established that TMP105 QOM temperature changes propagate to Linux hwmon and Redfish.

The earlier 30-sample constant-temperature capture does not prove a stuck-sensor fault because the sensor input was deliberately held constant. A proper fault experiment must demonstrate that the expected temperature changes while the reported sensor output remains fixed.

No TMP105 source patch has been applied yet.

## 9. Next steps
1. Preserve this checkpoint and verify its contents.
2. Inspect the TMP105 source and current VMState implementation before making changes.
3. Implement an emulator-level stuck-output control in the separate source tree/build workflow.
4. Ensure enabling the fault captures the current sensor output and subsequent input changes do not alter the reported output.
5. Ensure disabling the fault restores normal reporting.
6. Review migration/VMState implications before finalizing the implementation.
7. Build and test using the independent build directory.
8. Do not launch a second guest or disturb PID 9633 until a separate test plan is agreed.
9. Validate the fault using an independently changing expected temperature, timestamped hwmon/Redfish telemetry, labels, and recovery samples.
10. Preserve source changes, build commands, outputs, datasets, plots, and reproducibility instructions in the project repository.

## 10. Safety and preservation rules
- Do not stop or restart PID 9633 without explicit planning.
- Do not overwrite the recovered executable.
- Do not configure or build in the original build directory.
- Use build-stuck-sensor-system for the independent build.
- Keep the recovered original and new executable hashes separate.
- Do not describe the preliminary constant-reading capture as a validated stuck-sensor fault.
