# ML Experiment Summary

Date: 2026-11-24

## 1. Objective

Summarize the controlled threshold experiments and assess the
feasibility of machine-learning anomaly detectors using the
available AST2600 emulated BMC telemetry datasets.

## 2. Controlled threshold experiments

### ADC0 voltage sag

- Samples: 140
- True negatives: 40
- False positives: 0
- False negatives: 0
- True positives: 100
- Accuracy: 1.00
- Precision: 1.00
- Recall: 1.00
- F1: 1.00
- False-alarm rate: 0.00

The normal standard deviation was zero, producing an exact
12.0 V comparison. Normal fitting samples were reused during
evaluation, so this is not independent test performance.

### Thermal fault

- Samples: 150
- True negatives: 120
- False positives: 0
- False negatives: 0
- True positives: 30
- Accuracy: 1.00
- Precision: 1.00
- Recall: 1.00
- F1: 1.00
- False-alarm rate: 0.00

Ground truth and predictions were aligned by source_file.
The result represents controlled temperature operating points,
not generalization to unseen hardware or natural workloads.

## 3. Isolation Forest feasibility

Isolation Forest was evaluated using normal-only fitting and
normal-validation-derived score thresholds.

The current ADC0 and thermal configurations did not produce
useful separation between normal and controlled fault samples.

This is a dataset/configuration limitation and is not evidence
that Isolation Forest is generally ineffective.

Detailed evidence:
evidence/phase_1/ml_experiments/isolation_forest_feasibility_20261124.md

## 4. LSTM feasibility

The existing bidirectional LSTM autoencoder uses a 30-sample
window.

ADC0 normal captures contain only 20 samples each.
Thermal normal captures contain 30 constant samples each.

The available data does not provide sufficient independent,
diverse normal sequences for credible training and validation.

LSTM training and performance claims were therefore deferred.

Detailed evidence:
evidence/phase_1/ml_experiments/lstm_feasibility_20261124.md

## 5. Evaluation pipeline

The new evaluator is:
code/evaluate_controlled_experiments.py

It validates source-file alignment, binary labels, per-source
consistency and sample counts.

Outputs:
- results/controlled_experiment_metrics_20261124.csv
- results/controlled_experiment_phase_summary_20261124.csv

ADC0 and thermal experiments are reported separately.
No pooled cross-experiment metric is calculated.

## 6. Overall conclusion

The project demonstrates BMC telemetry collection and
controlled anomaly detection using threshold-based methods
for ADC0 voltage sag and thermal fault scenarios.

Isolation Forest and LSTM were assessed for feasibility.
The current datasets do not support strong ML performance
claims for these models.

The results are proof-of-concept findings from a QEMU-emulated
AST2600 OpenBMC environment. They do not establish performance
on physical servers or arbitrary real-world workloads.

## 7. Reproducibility and preservation

The original detector scripts, historical verdict files,
processed datasets and experiment-specific reports are preserved.

The unified evaluation script and its outputs use new filenames.
No historical results were overwritten.
