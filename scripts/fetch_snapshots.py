#!/usr/bin/env python
"""Fetch and seal weekly EPSS + KEV snapshots for the §3.3 target.

Examples (run from /mnt/c/Research/ANFIS with venv active):
  python scripts/fetch_snapshots.py fetch --start 2025-09-01 --end 2026-09-21
  python scripts/fetch_snapshots.py status --start 2025-09-01 --end 2026-09-21
  python scripts/fetch_snapshots.py verify
Default output root: data/real/snapshots (epss/, kev/, manifest.json).
Exit code is non-zero on any integrity failure (fail-closed).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from python_hanfis import snapshots as S  # noqa: E402


def _date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def cmd_fetch(a: argparse.Namespace) -> int:
    root = Path(a.out)
    manifest = S.load_manifest(root)
    grid = S.monday_grid(a.start, a.end)
    todo = [d for d in grid if a.force or d.isoformat() not in manifest["epss"]]
    print(f"grid: {len(grid)} Mondays {grid[0]}..{grid[-1]}; to fetch: {len(todo)}")
    failures: list[str] = []
    if not a.kev_only:
        for i, d in enumerate(todo, 1):
            for attempt in range(1, a.retries + 1):
                try:
                    snap = S.fetch_epss(d, root / "epss")
                    S.record_epss(manifest, snap, root)
                    S.save_manifest(root, manifest)   # checkpoint after every file
                    print(f"[{i}/{len(todo)}] EPSS {d}  rows={snap.n_rows}  model={snap.model_version}  sha256={snap.sha256[:12]}")
                    break
                except S.SnapshotError as exc:
                    print(f"[{i}/{len(todo)}] EPSS {d} INTEGRITY FAILURE (not retried): {exc}")
                    failures.append(f"{d}: {exc}")
                    break
                except Exception as exc:  # network / IO: retry with backoff
                    if attempt == a.retries:
                        print(f"[{i}/{len(todo)}] EPSS {d} FAILED after {a.retries} attempts: {exc}")
                        failures.append(f"{d}: {exc}")
                    else:
                        time.sleep(a.backoff * attempt)
            time.sleep(a.pause)
    if not a.epss_only:
        try:
            snap = S.fetch_kev(root / "kev")
            S.record_kev(manifest, snap, root)
            S.save_manifest(root, manifest)
            print(f"KEV catalog {snap.catalog_version}  entries={snap.n_entries}  sha256={snap.sha256[:12]}")
        except Exception as exc:
            print(f"KEV FAILED: {exc}")
            failures.append(f"KEV: {exc}")
    S.verify_manifest(root)
    print(json.dumps(S.status(root, a.start, a.end), indent=2))
    if failures:
        print(f"STATUS=FAIL_SNAPSHOTS ({len(failures)} failures)")
        return 1
    print("STATUS=PASS_SNAPSHOTS")
    return 0


def cmd_status(a: argparse.Namespace) -> int:
    st = S.status(Path(a.out), a.start, a.end)
    print(json.dumps(st, indent=2))
    print("STATUS=SEALED" if st["sealed"] else "STATUS=INCOMPLETE")
    return 0 if st["sealed"] else 1


def cmd_verify(a: argparse.Namespace) -> int:
    m = S.verify_manifest(Path(a.out))
    print(f"manifest OK: {len(m['epss'])} EPSS files, {len(m['kev'])} KEV files, all hashes match")
    print("STATUS=VERIFIED")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default=str(ROOT / "data" / "real" / "snapshots"))
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch"); f.add_argument("--start", type=_date, required=True); f.add_argument("--end", type=_date, required=True)
    f.add_argument("--force", action="store_true"); f.add_argument("--epss-only", action="store_true"); f.add_argument("--kev-only", action="store_true")
    f.add_argument("--retries", type=int, default=3); f.add_argument("--backoff", type=float, default=5.0); f.add_argument("--pause", type=float, default=1.0)
    f.set_defaults(fn=cmd_fetch)
    s = sub.add_parser("status"); s.add_argument("--start", type=_date, required=True); s.add_argument("--end", type=_date, required=True); s.set_defaults(fn=cmd_status)
    v = sub.add_parser("verify"); v.set_defaults(fn=cmd_verify)
    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except S.SnapshotError as exc:
        print(f"{exc}\nSTATUS=FAIL_INTEGRITY")
        return 2


if __name__ == "__main__":
    sys.exit(main())
