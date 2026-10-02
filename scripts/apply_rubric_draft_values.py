#!/usr/bin/env python
"""Fills proposed_kubernetes_exposure, proposed_asset_criticality, and
proposed_mfa_risk in configs/assets_candidates_toward120.csv with the
rubric-derived DRAFT values from catatan_keputusan_20261002.md section 4
(kubernetes_exposure/asset_criticality) and the follow-up mfa_risk rubric
given in chat on 2026-10-02 (infrastructure-MFA framing: does compromising
this component bypass MFA protecting something else, rather than "does it
have its own MFA login" -- none of the 11 candidates have a human login path
at all, so the literal question doesn't apply to any of them).

This is a draft-filling convenience, not a final decision: it prints a
before/after diff for every row it changes, and the values it writes are
exactly the ones already shown to Hafiz for review -- nothing here is
computed fresh or hidden. Hafiz can hand-edit the CSV afterward to override
any value before running scripts/merge_candidates_into_assets.py.

Usage: scripts/apply_rubric_draft_values.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_CSV = ROOT / "configs" / "assets_candidates_toward120.csv"

# asset_id -> (kubernetes_exposure, asset_criticality, mfa_risk)
# ke/ac from catatan_keputusan_20261002.md section 4; mfa_risk from the
# infrastructure-MFA rubric given in chat 2026-10-02 (0 = machine-to-machine
# auth only, no reusable human-equivalent credential; 0.5 = holds a reusable
# identity/signing credential but not SSO/IdP itself; 1 = directly manages
# SSO/IdP-equivalent credentials, compromise bypasses MFA entirely elsewhere).
DRAFT_VALUES = {
    "etcd-3-5":                ("0.5", "7", "0"),
    "opa-0-70":                ("0.5", "4", "0"),
    "gatekeeper-3-17":         ("1",   "5", "0"),
    "cilium-1-16":             ("1",   "6", "0"),
    "istio-proxy-1-23":        ("1",   "3", "0.5"),
    "kafka-3-8":               ("0.5", "4", "0"),
    "velero-1-15":             ("0.5", "6", "0.5"),
    "metrics-server-0-7":      ("0.5", "2", "0"),
    "cosign-2-4":              ("0",   "1", "0.5"),
    "external-secrets-0-10":   ("0.5", "5", "1"),
    "kube-state-metrics-2-13": ("0.5", "1", "0"),
}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="print the diff, write nothing")
    a = p.parse_args(argv)

    if not CANDIDATES_CSV.exists():
        raise SystemExit(f"ABORT: {CANDIDATES_CSV} does not exist.")

    with CANDIDATES_CSV.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
        fieldnames = list(rows[0].keys()) if rows else []

    missing = {r["asset_id"] for r in rows} - set(DRAFT_VALUES)
    if missing:
        print(f"WARNING: no draft values known for: {sorted(missing)} -- left untouched.")

    changes = []
    for row in rows:
        aid = row["asset_id"]
        if aid not in DRAFT_VALUES:
            continue
        ke_new, ac_new, mfa_new = DRAFT_VALUES[aid]
        ke_old = row.get("proposed_kubernetes_exposure", "")
        ac_old = row.get("proposed_asset_criticality", "")
        mfa_old = row.get("proposed_mfa_risk", "")
        if ke_old != ke_new or ac_old != ac_new or mfa_old != mfa_new:
            changes.append((aid, ke_old, ke_new, ac_old, ac_new, mfa_old, mfa_new))
            row["proposed_kubernetes_exposure"] = ke_new
            row["proposed_asset_criticality"] = ac_new
            row["proposed_mfa_risk"] = mfa_new

    if not changes:
        print("No changes to make (already applied, or no matching asset_id).")
        return 0

    print(f"{len(changes)} row(s) would change:")
    for aid, ke_old, ke_new, ac_old, ac_new, mfa_old, mfa_new in changes:
        print(f"  {aid}: kubernetes_exposure '{ke_old}' -> '{ke_new}', asset_criticality '{ac_old}' -> '{ac_new}', "
              f"mfa_risk '{mfa_old}' -> '{mfa_new}'")

    if a.dry_run:
        print("\n--dry-run: not writing anything.")
        return 0

    with CANDIDATES_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {CANDIDATES_CSV}. Review with git diff before trusting these as final.")
    print("STATUS=DRAFT_VALUES_APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
