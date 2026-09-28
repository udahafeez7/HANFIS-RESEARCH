"""Sealed weekly EPSS / CISA-KEV snapshots for the §3.3 temporal target.

Design (fail-closed, per the 2026-09-21 quality memo):
- One EPSS snapshot per Monday: the FIRST.org daily bulk file for that date,
  stored byte-for-byte as downloaded (gzip) and sealed with SHA-256.
- One KEV catalogue download, sealed; any historical "as-of" view is
  reconstructed from ``dateAdded`` <= snapshot date (see ``kev_as_of``).
- ``manifest.json`` records url, sha256, bytes, fetched_at, row counts.
  ``verify_manifest`` recomputes every hash and refuses to pass on any
  mismatch or missing file. Nothing downstream may read a snapshot that
  is not in a verified manifest.

Network access is injected (``opener``) so every parsing/sealing path is
unit-testable offline; the real opener is ``urllib``.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

EPSS_URL = "https://epss.cyentia.com/epss_scores-{date}.csv.gz"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
MIN_EPSS_ROWS = 100_000          # FIRST publishes >200k CVEs/day; below this the file is truncated
MIN_KEV_ENTRIES = 1_000          # KEV has held >1,000 entries since 2023
MANIFEST_NAME = "manifest.json"
Opener = Callable[[str], bytes]


class SnapshotError(RuntimeError):
    """Raised on any integrity failure. Never caught inside this module."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def urllib_opener(url: str, timeout: float = 120.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "HANFIS-snapshots/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https hosts)
        if resp.status != 200:
            raise SnapshotError(f"HTTP {resp.status} for {url}")
        return resp.read()


def monday_grid(start: dt.date, end: dt.date) -> list[dt.date]:
    """All Mondays d with start <= d <= end (inclusive). start/end need not be Mondays."""
    if end < start:
        raise SnapshotError(f"end {end} precedes start {start}")
    first = start + dt.timedelta(days=(7 - start.weekday()) % 7)
    out, d = [], first
    while d <= end:
        out.append(d)
        d += dt.timedelta(days=7)
    return out


# ----------------------------------------------------------------------------- EPSS
_EPSS_HEADER = re.compile(r"#model_version:(?P<model>[^,]+),score_date:(?P<date>\d{4}-\d{2}-\d{2})")


@dataclass(frozen=True)
class EpssSnapshot:
    date: dt.date
    model_version: str
    n_rows: int
    sha256: str
    path: Path


def parse_epss_gz(raw: bytes, expected_date: dt.date) -> tuple[str, int]:
    """Validate a FIRST bulk file. Returns (model_version, n_rows). Fail-closed."""
    try:
        text = gzip.decompress(raw).decode("utf-8")
    except (OSError, EOFError, UnicodeDecodeError) as exc:
        raise SnapshotError(f"EPSS {expected_date}: not a valid gzip/UTF-8 file ({exc})") from exc
    lines = text.splitlines()
    if len(lines) < 2:
        raise SnapshotError(f"EPSS {expected_date}: empty file")
    m = _EPSS_HEADER.match(lines[0])
    if not m:
        raise SnapshotError(f"EPSS {expected_date}: missing/invalid header comment: {lines[0][:80]!r}")
    if m.group("date") != expected_date.isoformat():
        raise SnapshotError(f"EPSS {expected_date}: header score_date {m.group('date')} != requested date")
    reader = csv.reader(lines[1:])
    header = next(reader)
    if header[:3] != ["cve", "epss", "percentile"]:
        raise SnapshotError(f"EPSS {expected_date}: unexpected columns {header[:3]}")
    n = 0
    for row in reader:
        if not row:
            continue
        if not row[0].startswith("CVE-"):
            raise SnapshotError(f"EPSS {expected_date}: bad CVE id at row {n + 1}: {row[0]!r}")
        p = float(row[1])
        if not 0.0 <= p <= 1.0:
            raise SnapshotError(f"EPSS {expected_date}: score out of [0,1] at {row[0]}: {p}")
        n += 1
    return m.group("model"), n


def fetch_epss(date: dt.date, out_dir: Path, opener: Opener = urllib_opener,
               min_rows: int = MIN_EPSS_ROWS) -> EpssSnapshot:
    url = EPSS_URL.format(date=date.isoformat())
    raw = opener(url)
    model, n = parse_epss_gz(raw, date)
    if n < min_rows:
        raise SnapshotError(f"EPSS {date}: only {n} rows (< {min_rows}); refusing truncated file")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"epss_scores-{date.isoformat()}.csv.gz"
    path.write_bytes(raw)
    return EpssSnapshot(date, model, n, sha256_bytes(raw), path)


def load_epss(path: Path):
    """Read a sealed EPSS file into a DataFrame [cve, epss, percentile]. Caller must verify manifest first."""
    import pandas as pd
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return pd.read_csv(fh, comment="#", dtype={"cve": "string", "epss": "float64", "percentile": "float64"})


# ----------------------------------------------------------------------------- KEV
@dataclass(frozen=True)
class KevSnapshot:
    fetched_at: dt.datetime
    catalog_version: str
    n_entries: int
    sha256: str
    path: Path


def parse_kev_json(raw: bytes) -> tuple[str, list[dict]]:
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"KEV: invalid JSON ({exc})") from exc
    entries = doc.get("vulnerabilities")
    if not isinstance(entries, list):
        raise SnapshotError("KEV: 'vulnerabilities' list missing")
    if int(doc.get("count", -1)) != len(entries):
        raise SnapshotError(f"KEV: count {doc.get('count')} != len(vulnerabilities) {len(entries)}")
    for e in entries:
        if not str(e.get("cveID", "")).startswith("CVE-"):
            raise SnapshotError(f"KEV: bad cveID {e.get('cveID')!r}")
        dt.date.fromisoformat(e["dateAdded"])  # raises ValueError -> propagate as integrity failure
    return str(doc.get("catalogVersion", "")), entries


def fetch_kev(out_dir: Path, opener: Opener = urllib_opener, now: dt.datetime | None = None,
              min_entries: int = MIN_KEV_ENTRIES) -> KevSnapshot:
    raw = opener(KEV_URL)
    version, entries = parse_kev_json(raw)
    if len(entries) < min_entries:
        raise SnapshotError(f"KEV: only {len(entries)} entries (< {min_entries})")
    now = now or dt.datetime.now(dt.timezone.utc)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"kev-{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_bytes(raw)
    return KevSnapshot(now, version, len(entries), sha256_bytes(raw), path)


def kev_as_of(entries: Iterable[dict], date: dt.date) -> set[str]:
    """CVE ids present in KEV on ``date`` (dateAdded <= date).

    Limitation (state in the manuscript): CISA rarely removes entries; a removed
    entry is absent from a later download and thus from every reconstructed
    week. This is conservative (fewer positives), never inflating labels.
    """
    return {e["cveID"] for e in entries if dt.date.fromisoformat(e["dateAdded"]) <= date}


# ----------------------------------------------------------------------------- manifest
def load_manifest(root: Path) -> dict:
    p = root / MANIFEST_NAME
    if not p.exists():
        return {"schema": 1, "epss": {}, "kev": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def save_manifest(root: Path, manifest: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / (MANIFEST_NAME + ".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(root / MANIFEST_NAME)


def record_epss(manifest: dict, snap: EpssSnapshot, root: Path) -> None:
    manifest["epss"][snap.date.isoformat()] = {
        "file": str(snap.path.relative_to(root)), "sha256": snap.sha256, "bytes": snap.path.stat().st_size,
        "model_version": snap.model_version, "n_rows": snap.n_rows,
        "url": EPSS_URL.format(date=snap.date.isoformat()),
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


def record_kev(manifest: dict, snap: KevSnapshot, root: Path) -> None:
    manifest["kev"][snap.fetched_at.strftime("%Y%m%dT%H%M%SZ")] = {
        "file": str(snap.path.relative_to(root)), "sha256": snap.sha256, "bytes": snap.path.stat().st_size,
        "catalog_version": snap.catalog_version, "n_entries": snap.n_entries, "url": KEV_URL,
        "fetched_at": snap.fetched_at.isoformat(timespec="seconds"),
    }


def verify_manifest(root: Path) -> dict:
    """Recompute every hash. Returns the manifest; raises SnapshotError on ANY discrepancy."""
    manifest = load_manifest(root)
    problems: list[str] = []
    for section in ("epss", "kev"):
        for key, rec in manifest.get(section, {}).items():
            p = root / rec["file"]
            if not p.exists():
                problems.append(f"{section}:{key}: file missing {p}")
                continue
            if p.stat().st_size != rec["bytes"]:
                problems.append(f"{section}:{key}: size {p.stat().st_size} != {rec['bytes']}")
            if sha256_file(p) != rec["sha256"]:
                problems.append(f"{section}:{key}: sha256 mismatch")
    if problems:
        raise SnapshotError("manifest verification FAILED:\n  " + "\n  ".join(problems))
    return manifest


def status(root: Path, start: dt.date, end: dt.date) -> dict:
    """Coverage report for the Monday grid; never raises on missing weeks (that is the report)."""
    manifest = verify_manifest(root)
    grid = monday_grid(start, end)
    have = {d for d in grid if d.isoformat() in manifest["epss"]}
    missing = [d.isoformat() for d in grid if d not in have]
    kev_keys = sorted(manifest["kev"])
    return {
        "weeks_expected": len(grid), "weeks_present": len(have), "weeks_missing": missing,
        "coverage": round(len(have) / len(grid), 4) if grid else 0.0,
        "kev_downloads": len(kev_keys),
        "kev_latest": manifest["kev"][kev_keys[-1]] if kev_keys else None,
        "sealed": not missing and bool(kev_keys),
    }
