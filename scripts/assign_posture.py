#!/usr/bin/env python
"""Deterministic, balanced posture factorial for scan-only assets (§3.3 randomized posture factorial).

Levels: x4 mfa_risk {0, 0.5, 1} x x5 kubernetes_exposure {0, 0.5, 1} x x6 asset_criticality {1..5} = 45 cells.
Assets are assigned cells from a seeded permutation, so the first 45 assets cover every cell once and the
assignment of an existing asset never changes when new assets are added (position = order in the inventory).
rho: scan-only assets have no runtime reachability evidence; default_rho is a stated assumption (A-01 level
0.1 = installed, dependency unknown) recorded in the protocol column, never silently.

  python scripts/assign_posture.py append --asset-id redis-7-alpine --image-id "docker.io/library/redis@sha256:..." \
         --scan-json data/evidence/redis-7-alpine_trivy_scan_XXXX/redis-7-alpine_vulnerabilities.json
  python scripts/assign_posture.py show --n 24
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "configs" / "assets.csv"
COLUMNS = ("asset_id", "image_id", "scan_json", "mfa_risk", "kubernetes_exposure", "asset_criticality",
           "default_rho", "package_rho_json", "protocol")
CELLS = list(itertools.product((0.0, 0.5, 1.0), (0.0, 0.5, 1.0), (1, 2, 3, 4, 5)))   # 45
SEED = 20260928


def cell_for(position: int, seed: int = SEED) -> tuple[float, float, int]:
    """Cell for the asset at 0-based inventory position; a full permutation every 45 assets."""
    block, idx = divmod(position, len(CELLS))
    order = list(range(len(CELLS)))
    random.Random(seed + block).shuffle(order)
    return CELLS[order[idx]]


def read_assets(path: Path = ASSETS) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def append_asset(asset_id: str, image_id: str, scan_json: str, default_rho: float, protocol: str,
                 path: Path = ASSETS, seed: int = SEED) -> dict:
    rows = read_assets(path)
    if any(r["asset_id"] == asset_id for r in rows):
        raise SystemExit(f"ABORT: asset_id {asset_id} already in {path}")
    if "@sha256:" not in image_id:
        raise SystemExit(f"ABORT: image_id must be digest-pinned: {image_id}")
    if not (ROOT / scan_json).exists():
        raise SystemExit(f"ABORT: scan_json not found: {scan_json}")
    scan_only = [r for r in rows if r["protocol"].startswith("scan-only")]
    x4, x5, x6 = cell_for(len(scan_only), seed)
    row = {"asset_id": asset_id, "image_id": image_id, "scan_json": scan_json, "mfa_risk": x4,
           "kubernetes_exposure": x5, "asset_criticality": x6, "default_rho": default_rho,
           "package_rho_json": "{}", "protocol": protocol}
    with path.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        if fh.tell() == 0:
            w.writeheader()
        w.writerow(row)
    return row


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("append")
    a.add_argument("--asset-id", required=True); a.add_argument("--image-id", required=True); a.add_argument("--scan-json", required=True)
    a.add_argument("--default-rho", type=float, default=0.1); a.add_argument("--protocol", default="scan-only-v1-rho0.1-assumed")
    a.add_argument("--assets", default=str(ASSETS)); a.add_argument("--seed", type=int, default=SEED)
    s = sub.add_parser("show"); s.add_argument("--n", type=int, default=45); s.add_argument("--seed", type=int, default=SEED)
    args = p.parse_args(argv)
    if args.cmd == "show":
        for i in range(args.n):
            print(i, cell_for(i, args.seed))
        return 0
    row = append_asset(args.asset_id, args.image_id, args.scan_json, args.default_rho, args.protocol, Path(args.assets), args.seed)
    print("APPENDED " + json.dumps(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
