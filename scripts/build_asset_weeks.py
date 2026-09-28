#!/usr/bin/env python
"""Build the contract-v2 asset-week table from Trivy evidence + sealed snapshots.

  python scripts/build_asset_weeks.py --start 2025-08-25 --end 2026-09-21
  python scripts/build_asset_weeks.py --start ... --end ... --only p0-baseline
Inputs : configs/assets.csv, data/real/snapshots/ (must be SEALED)
Outputs: data/processed/asset_weeks_v2.csv, .jsonl, _diagnostics.csv, _status.json
Prints the three mandatory daily numbers and STATUS=TRAINING_AUTHORIZED|HOLD.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from python_hanfis import asset_weeks as AW  # noqa: E402
from python_hanfis import snapshots as S  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--assets", default=str(ROOT / "configs" / "assets.csv"))
    p.add_argument("--snapshots", default=str(ROOT / "data" / "real" / "snapshots"))
    p.add_argument("--schema", default=str(ROOT / "configs" / "anfis_source_schema_v2.json"))
    p.add_argument("--out-prefix", default=str(ROOT / "data" / "processed" / "asset_weeks_v2"))
    p.add_argument("--start", type=dt.date.fromisoformat, required=True)
    p.add_argument("--end", type=dt.date.fromisoformat, required=True)
    p.add_argument("--only", action="append", default=None, help="restrict to these asset_id(s)")
    p.add_argument("--horizon-days", type=int, default=30)
    p.add_argument("--s-no-rho", action="store_true", help="label S_{v,a}=1 instead of rho_v")
    a = p.parse_args(argv)
    try:
        assets = AW.load_assets(Path(a.assets), ROOT)
        if a.only:
            assets = [x for x in assets if x.asset_id in set(a.only)]
            if not assets:
                raise AW.AssetWeekError(f"--only matched no asset in {a.assets}")
        store = AW.SnapshotStore(Path(a.snapshots))
        weeks = S.monday_grid(a.start, a.end)
        spec = AW.LabelSpec(horizon_days=a.horizon_days, s_uses_rho=not a.s_no_rho)
        rows, diags = AW.build_rows(assets, store, weeks, spec)
        problems = AW.validate_contract(rows, json.loads(Path(a.schema).read_text(encoding="utf-8")))
        if problems:
            print("\n".join(problems[:20]))
            print(f"STATUS=FAIL_CONTRACT ({len(problems)} violations)")
            return 2
    except (AW.AssetWeekError, S.SnapshotError) as exc:
        print(f"{exc}\nSTATUS=FAIL_BUILD")
        return 2
    out = Path(a.out_prefix); out.parent.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    with (out.parent / (out.name + ".csv")).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
    with (out.parent / (out.name + ".jsonl")).open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    with (out.parent / (out.name + "_diagnostics.csv")).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(diags[0].keys())); w.writeheader(); w.writerows(diags)
    st = AW.gate_status(rows)
    st.update({"built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "weeks": len(weeks),
               "start": a.start.isoformat(), "end": a.end.isoformat(), "kev_catalog": store.kev_version,
               "epss_model_versions": sorted({d["epss_model_version"] for d in diags}), "label_spec": spec.__dict__})
    (out.parent / (out.name + "_status.json")).write_text(json.dumps(st, indent=2), encoding="utf-8")
    print(f"wrote {out}.csv/.jsonl/_diagnostics.csv/_status.json")
    print(f"TIGA ANGKA WAJIB: baris event_id={st['n_rows_event_id']}  non-NA={st['share_non_na']:.3f}  "
          f"positif={st['share_positive']:.3f}  aset={st['n_assets']}  INSUFFICIENT={st['n_insufficient']}")
    print(json.dumps(st["checks"], indent=2))
    print("STATUS=" + ("TRAINING_AUTHORIZED" if st["TRAINING_AUTHORIZED"] else "HOLD_TRAINING"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
