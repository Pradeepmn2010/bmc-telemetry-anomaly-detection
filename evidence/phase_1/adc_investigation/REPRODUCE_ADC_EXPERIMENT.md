# Reproducing the ADC hwmon and D-Bus experiment

## Prerequisites

- AST2600 OpenBMC QEMU emulator booted.
- SSH access to BMC on localhost port 2222.
- busctl available on the BMC.
- Linux hwmon device iio_hwmon available.
- ADC sensor process running.
- ADC Entity Manager configuration present.

## Step 1: Connect to BMC

From Ubuntu/WSL:

    ssh -p 2222 root@127.0.0.1

## Step 2: Verify ADC service

    busctl --system list | grep ADCSensor
    ps | grep '[a]dcsensor'
    cat /sys/class/hwmon/hwmon18/name

Identify the current unique D-Bus name from the service listing.
Do not assume it will always be :1.48.

## Step 3: Verify Entity Manager configuration

    sed -n '40,140p' \
      /usr/share/entity-manager/configurations/ast2600-evb.json

Record the Index and ScaleFactor for ADC0_12V and ADC8_12V.

## Step 4: Capture five samples

Replace DBUS_NAME with the current unique name.

    DBUS_NAME=:1.48

    for n in 1 2 3 4 5; do
        echo "=== Sample $n ==="

        for i in 1 9; do
            printf 'in%s_input (mV)=' "$i"
            cat "/sys/class/hwmon/hwmon18/in${i}_input"
        done

        for s in ADC0_12V ADC8_12V; do
            printf '%s=' "$s"
            busctl --system get-property \
              "$DBUS_NAME" \
              "/xyz/openbmc_project/sensors/voltage/$s" \
              xyz.openbmc_project.Sensor.Value Value
        done

        sleep 1
    done

## Step 5: Preserve raw output

On the BMC, save output under /tmp and transfer it to the
project repository using SCP.

Example transfer from Ubuntu:

    mkdir -p evidence/phase_1/adc_investigation

    scp -P 2222 \
      root@127.0.0.1:/tmp/EXPERIMENT_LOG.log \
      evidence/phase_1/adc_investigation/

## Step 6: Verify evidence integrity

    sha256sum evidence/phase_1/adc_investigation/*.log

Preserve original raw logs unchanged.

## Safety and reproducibility notes

- Do not restart QEMU, D-Bus, or adcsensor during a measurement run.
- Readings change rapidly; measurements are sequential.
- Record the firmware version, QEMU version, timestamp, service PID,
  and unique D-Bus name for each run.
- Never assume a previous unique D-Bus name remains valid.
- Do not interpret emulator-generated sensor readings as physical
  hardware measurements.
- Record errors and failed measurements rather than silently
  discarding them.

---

## Experiment 2: Raw ADC, D-Bus voltage and high-side alarms

Use the existing SSH connection to the BMC.

First identify the current ADC D-Bus unique name:

    busctl --system list | grep ADCSensor

Do not assume the previous unique name is still valid.

Verify the hwmon inputs:

    cat /sys/class/hwmon/hwmon18/in1_input
    cat /sys/class/hwmon/hwmon18/in9_input

For each sample, collect:

- UTC timestamp
- ADC0 raw hwmon value
- ADC8 raw hwmon value
- ADC0 D-Bus voltage
- ADC0 WarningAlarmHigh
- ADC0 CriticalAlarmHigh
- ADC8 D-Bus voltage
- ADC8 WarningAlarmHigh
- ADC8 CriticalAlarmHigh

Use 30 iterations with a nominal two-second sleep interval.

The reads are sequential. Record the actual timestamps and do not
treat the values as simultaneous measurements.

Validate the transferred CSV on the host:

- Check the expected nine columns.
- Check the measurement row count.
- Check for missing fields.
- Validate Boolean alarm fields.
- Calculate and record SHA-256.

Preserve every raw experiment separately. Do not overwrite the
original five-sample evidence.
