# HANFIS Source Gate v1.2

This package separates external FuzzyFortify reference cases from trainable
ANFIS/HANFIS events. It never fills missing values and fails closed whenever
primary evidence or a required feature is absent.

## Current checkpoint

`hanfis_source_intake_v1_1.csv` contains five FuzzyFortify reference cases.
They remain `external_reference_only` and are not eligible for training.

## 1. Produce row-level QC

```bash
python audit_source_intake_v1_2.py \
  --input "/mnt/c/Research/ANFIS/data/real/hanfis_source_intake_v1_1.csv" \
  --contract source_contract_v1_2.json \
  --qc-output source_intake_qc_v1_2.csv
```

Expected current result: `STATUS=HOLD_SOURCE_INTAKE_QC`, with five held rows.

## 2. Promotion gate

Run this only on a separately completed primary-event intake file. Do not use
the five reference-only FuzzyFortify rows.

```bash
python validate_and_promote_source_v1_2.py \
  --input "/mnt/c/Research/ANFIS/data/real/hanfis_primary_event_intake_v1_2.csv" \
  --contract source_contract_v1_2.json \
  --output "/mnt/c/Research/ANFIS/data/real/hanfis_source_data_v1_2.csv"
```

Only `STATUS=PASS_SOURCE_PROMOTION_V1_2` authorizes expert labeling. Expert
labels still require at least three independent, model-blind labelers for every
`event_id`.

## Scientific boundary

- Telemetry is evaluated as system performance/footprint evidence, not as the
  risk target.
- FuzzyFortify published outputs are reference results, not ANFIS/HANFIS labels.
- No row may enter training without traceable primary evidence.
- Matplotlib comparison figures are generated only from gated result tables.
