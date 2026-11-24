# LSTM Autoencoder Feasibility Assessment

Date: 2026-11-24

## 1. Objective

Assess whether the available ADC0 and thermal datasets support
meaningful LSTM reconstruction autoencoder training and evaluation.

## 2. Existing implementation

Script: code/detect_lstm.py

Configuration:
- Window size: 30 samples
- Epochs: 20
- Batch size: 64
- Hidden units: 32
- Learning rate: 0.001
- Threshold: 99th percentile of normal reconstruction error

The model is a bidirectional LSTM reconstruction autoencoder.

## 3. Dataset assessment

### ADC0

- Total normal samples: 40
- Baseline capture: 20 samples
- Nominal recovery capture: 20 samples
- Distinct ADC0 readings within each capture: 1
- Required window size: 30

Neither normal capture independently contains enough samples
to construct one complete window.

### Thermal

- Total normal samples: 120
- Four separate normal captures
- 30 samples per capture
- Each capture contains one distinct temperature reading
- Required window size: 30

Only one window can be formed per capture when session boundaries
are respected. This provides four highly repetitive windows,
which is insufficient for credible sequence-model training.

## 4. Implementation limitations

1. The numeric feature selector excludes timestamp and label,
   but does not explicitly exclude anomaly_label. This creates
   a ground-truth leakage risk when using current processed data.
2. The window-generation function does not preserve source-file
   boundaries. Concatenating separate captures could create
   artificial sequences.
3. ADC0 normal captures are shorter than the configured window.
4. Thermal captures provide only one window each and have no
   within-capture temperature variation.
5. The current datasets do not support a meaningful independent
   normal validation set for reconstruction-threshold selection.

## 5. Decision

LSTM training and performance evaluation are deferred.

No LSTM accuracy, precision, recall, F1 or false-alarm rate
will be reported from these datasets.

This is a data-readiness limitation, not evidence that LSTM
methods are generally ineffective.

## 6. Requirements for future LSTM evaluation

- Collect longer continuous normal telemetry sessions.
- Preserve capture and session identifiers.
- Ensure adequate natural variation in normal operating conditions.
- Split training, validation and test data by capture/session.
- Explicitly exclude labels and metadata from model features.
- Generate windows independently within each session.
- Derive reconstruction thresholds using normal validation data.
- Evaluate on separately collected, labelled fault sessions.

## 7. Preservation

The existing LSTM implementation was inspected but not modified.
No LSTM training was performed and no historical results were
overwritten.
