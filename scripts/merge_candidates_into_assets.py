#!/usr/bin/env python
"""Merges the 11 scanned candidate assets into configs/assets.csv (109 -> 120 rows),
once the judgment columns (mfa_risk, kubernetes_exposure, asset_criticality) in
configs/assets_candidates_toward120.csv have been filled in by hand.

Joins two files, neither of which alone has everything a row needs:
  - configs/assets_candidates_toward120.csv: asset_id, category, and the three
    judgment columns (filled by hand; this script refuses to proceed if any are
    still the ISI_HAFIZ placeholder)
  - configs/assets_candidates_toward120_scanresults.csv: asset_id, image_ref,
    bundle_dir, scan_json, db_frozen_ok, db_updated_at_seen (written by
    scripts/run_candidate_scans_20261001.sh)

Writes the result to configs/assets.csv, after backing up the original, and
refuses to proceed on ANY of the following (fail-closed, consistent with this
session's other data-pipeline scripts):
  - a judgment column still reads ISI_HAFIZ for any candidate
  - mfa_risk or kubernetes_exposure is not a valid number in [0, 1]
    (asset_criticality is NOT range-checked: the 109 existing rows show it on an
    unnormalised tier scale, e.g. up to 7, not [0,1] -- validating it there
    would be inventing a constraint the existing data doesn't follow)
  - an asset_id appears in one input file but not the other
  - any asset_id already exists in assets.csv (no silent duplicates/overwrites)
  - the scan_json path for any candidate does not exist on disk

istio-proxy-1-23's db_frozen_ok=DRIFTED (A-29: Trivy DB shifted to 2026-10-01 due
to a dropped TRIVY_SKIP_DB_UPDATE flag, unrecoverable) does NOT block the merge
-- it was a deliberate, disclosed decision, not an error to catch here. The
script prints a reminder of the disclosure requirement instead.

Usage: scripts/merge_candidates_into_assets.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS_CSV = ROOT / "configs" / "assets.csv"
CANDIDATES_CSV = ROOT / "configs" / "assets_candidates_toward120.csv"
SCANRESULTS_CSV = ROOT / "configs" / "assets_candidates_toward120_scanresults.csv"
JUDGMENT_COLS = ["proposed_mfa_risk", "proposed_kubernetes_exposure", "proposed_asset_criticality"]
ASSETS_COLS = ["asset_id", "image_id", "scan_json", "mfa_risk", "kubernetes_exposure",
               "asset_criticality", "default_rho", "package_rho_json", "protocol"]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"ABORT: {path} does not exist.")
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="validate and print the merge plan, write nothing")
    a = p.parse_args(argv)

    candidates = read_csv(CANDIDATES_CSV)
    scanresults = read_csv(SCANRESULTS_CSV)
    assets = read_csv(ASSETS_CSV)

    existing_ids = {r["asset_id"] for r in assets}
    cand_ids = {r["asset_id"] for r in candidates}
    scan_ids = {r["asset_id"] for r in scanresults}

    problems = []

    only_cand = cand_ids - scan_ids
    only_scan = scan_ids - cand_ids
    if only_cand:
        problems.append(f"{len(only_cand)} asset_id in candidates but not in scanresults: {sorted(only_cand)}")
    if only_scan:
        problems.append(f"{len(only_scan)} asset_id in scanresults but not in candidates: {sorted(only_scan)}")

    already_present = cand_ids & existing_ids
    if already_present:
        problems.append(f"{len(already_present)} candidate asset_id already exist in assets.csv -- "
                        f"refusing to duplicate/overwrite: {sorted(already_present)}")

    scan_by_id = {r["asset_id"]: r for r in scanresults}
    merged_rows = []
    for row in candidates:
        aid = row["asset_id"]
        for col in JUDGMENT_COLS:
            if row.get(col, "").strip().upper() == "ISI_HAFIZ" or not row.get(col, "").strip():
                problems.append(f"{aid}: column '{col}' is still ISI_HAFIZ or empty -- fill it before merging")
        for col in ("proposed_mfa_risk", "proposed_kubernetes_exposure"):
            val = row.get(col, "").strip()
            if val and val.upper() != "ISI_HAFIZ":
                try:
                    f = float(val)
                    if not (0.0 <= f <= 1.0):
                        problems.append(f"{aid}: {col}='{val}' is outside [0, 1]")
                except ValueError:
                    problems.append(f"{aid}: {col}='{val}' is not a number")

        sr = scan_by_id.get(aid)
        if sr is None:
            continue  # already reported above as only_cand
        scan_json_path = ROOT / sr["scan_json"]
        if not scan_json_path.exists():
            problems.append(f"{aid}: scan_json path does not exist: {scan_json_path}")
        if sr.get("db_frozen_ok") == "DRIFTED":
            print(f"NOTE: {aid} has db_frozen_ok=DRIFTED (db_updated_at_seen={sr.get('db_updated_at_seen')}) "
                  f"-- accepted per A-29 as a disclosed outlier, not blocking the merge. "
                  f"Remember to disclose this wherever results involving {aid} are cited.")

        merged_rows.append({
            "asset_id": aid,
            "image_id": sr["image_ref"],
            "scan_json": sr["scan_json"],
            "mfa_risk": row.get("proposed_mfa_risk", ""),
            "kubernetes_exposure": row.get("proposed_kubernetes_exposure", ""),
            "asset_criticality": row.get("proposed_asset_criticality", ""),
            "default_rho": row.get("default_rho", "0.1"),
            "package_rho_json": "{}",
            "protocol": row.get("protocol", "scan-only-v1-rho0.1-assumed"),
        })

    if problems:
        print(f"ABORT: {len(problems)} problem(s) found, nothing written:\n")
        for prob in problems:
            print(f"  - {prob}")
        return 2

    print(f"Validated {len(merged_rows)} candidate rows against {len(assets)} existing assets.csv rows "
          f"(result would be {len(assets) + len(merged_rows)}).")

    if a.dry_run:
        print("\n--dry-run: not writing anything.")
        for r in merged_rows:
            print(f"  {r['asset_id']}: image_id={r['image_id']}, mfa_risk={r['mfa_risk']}, "
                  f"kubernetes_exposure={r['kubernetes_exposure']}, asset_criticality={r['asset_criticality']}")
        return 0

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ASSETS_CSV.with_name(f"assets_backup_{stamp}.csv")
    shutil.copy2(ASSETS_CSV, backup)
    print(f"backed up original to {backup}")

    with ASSETS_CSV.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ASSETS_COLS, lineterminator="\n")
        for r in merged_rows:
            w.writerow(r)

    final_count = len(read_csv(ASSETS_CSV))
    print(f"wrote {len(merged_rows)} rows to {ASSETS_CSV}; final row count: {final_count}")
    if final_count != len(assets) + len(merged_rows):
        print(f"WARNING: expected {len(assets) + len(merged_rows)} rows but counted {final_count} -- "
              f"re-check the file before trusting it (possible header/formatting issue).")
        return 1
    print("STATUS=MERGE_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
