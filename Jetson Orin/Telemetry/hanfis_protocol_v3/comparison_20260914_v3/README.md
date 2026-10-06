# HANFIS comparison checkpoint

Run the FuzzyFortify reproduction audit:

```bash
python audit_fuzzyfortify_reproduction.py --output fuzzyfortify_reproduction_audit.csv
```

Expected current outcome is exit code 2 with
`STATUS=HOLD_FUZZYFORTIFY_REPRODUCTION_GAP`. This is an identified paper/code
reproduction issue, not a software crash.

Run native FuzzyFortify inference on a CSV containing the four required inputs:

```bash
python fuzzyfortify_baseline.py input.csv fuzzyfortify_predictions.csv
```

No automatic mapping from HANFIS features is performed.

Audit all candidate CSV files without loading their data rows:

```bash
python audit_comparison_dataset.py \
  "/mnt/c/Research/ANFIS/Jetson Orin/Telemetry" \
  --output comparison_data_inventory.csv \
  --allow-no-match
```

`HOLD_NO_STRICT_COMPARISON_DATASET` means that data construction is the next
milestone; it is not permission to substitute telemetry samples for risk labels.

Rank the nearest candidate CSV files after the inventory is produced:

```bash
python rank_comparison_candidates.py comparison_data_inventory.csv \
  --output comparison_candidate_ranking.csv --top 30
```

The Matplotlib pipeline is intentionally fail-closed and must only be invoked
after model metrics and event-level prediction files pass the common-key gates:

```bash
python plot_objective_comparison.py \
  --metrics metrics_per_repeat.csv \
  --predictions predictions_per_event.csv \
  --telemetry-pairs validated_telemetry_pairs.csv \
  --output figures
```
