#!/usr/bin/env python
"""Restores configs/assets_candidates_toward120.csv from the last git-committed
version (which has all 11 rows, confirmed intact by `git diff HEAD`), while
PRESERVING any judgment values already filled in the CURRENT working-copy file
for asset_ids that still exist there -- so today's manual edits are not lost
even though the file on disk had been truncated to 2 rows by some other,
unidentified cause (not this session's scripts: they only ever update existing
rows, never delete rows, and were only run against whatever was already on
disk at the time).

Usage: scripts/restore_candidates_csv.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] if (Path(__file__).resolve().parents[1] / ".git").exists() else Path.cwd()
CANDIDATES_CSV = ROOT / "configs" / "assets_candidates_toward120.csv"
JUDGMENT_COLS = ["proposed_mfa_risk", "proposed_kubernetes_exposure", "proposed_asset_criticality"]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)

    git_show = subprocess.run(
        ["git", "show", f"HEAD:{CANDIDATES_CSV.relative_to(ROOT)}"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if git_show.returncode != 0:
        raise SystemExit(f"ABORT: 'git show HEAD:...' failed:\n{git_show.stderr}")
    committed_rows = list(csv.DictReader(git_show.stdout.splitlines()))
    if len(committed_rows) < 2:
        raise SystemExit(f"ABORT: committed version only has {len(committed_rows)} row(s) -- "
                         f"that doesn't match the 11 rows expected; stopping rather than guessing.")

    current_rows = []
    if CANDIDATES_CSV.exists():
        with CANDIDATES_CSV.open(encoding="utf-8") as fh:
            current_rows = list(csv.DictReader(fh))
    current_by_id = {r["asset_id"]: r for r in current_rows}

    preserved = []
    for row in committed_rows:
        aid = row["asset_id"]
        cur = current_by_id.get(aid)
        if cur:
            changed_here = False
            for col in JUDGMENT_COLS:
                cur_val = cur.get(col, "").strip()
                if cur_val and cur_val.upper() != "ISI_HAFIZ" and cur_val != row.get(col, ""):
                    row[col] = cur_val
                    changed_here = True
            if changed_here:
                preserved.append(aid)
        else:
            print(f"NOTE: {aid} was in the committed version but not found in the current (truncated) "
                  f"working copy at all -- restoring it with its committed (likely ISI_HAFIZ) values.")

    extra_in_current = set(current_by_id) - {r["asset_id"] for r in committed_rows}
    if extra_in_current:
        print(f"WARNING: these asset_id exist in the current working copy but NOT in the committed "
              f"version -- not included in the restore, investigate separately: {sorted(extra_in_current)}")

    print(f"Restoring {len(committed_rows)} rows from git HEAD. "
          f"Preserving already-filled judgment values for: {preserved or 'none'}.")

    if a.dry_run:
        print("\n--dry-run: not writing anything. Preview:")
        for row in committed_rows:
            print(f"  {row['asset_id']}: mfa_risk={row['proposed_mfa_risk']}, "
                  f"kubernetes_exposure={row['proposed_kubernetes_exposure']}, "
                  f"asset_criticality={row['proposed_asset_criticality']}")
        return 0

    fieldnames = list(committed_rows[0].keys())
    with CANDIDATES_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        w.writerows(committed_rows)

    final = list(csv.DictReader(CANDIDATES_CSV.open(encoding="utf-8")))
    print(f"\nwrote {CANDIDATES_CSV}: {len(final)} rows.")
    if len(final) != 11:
        print(f"WARNING: expected 11 rows, got {len(final)} -- re-check before trusting this.")
        return 1
    print("STATUS=RESTORE_DONE -- now review with: git diff configs/assets_candidates_toward120.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
