"""Asset-week table (contract v2, A-12) from Trivy evidence bundles + sealed EPSS/KEV snapshots.

Layer: pipeline data (§3.3 target definition + kontrak data v2). One row per
(asset, ISO week). All temporal quantities are computed strictly from
information available at week_start (features) or inside (t, t+Δ] (label):

  active CVEs at date d   : scan CVEs with PublishedDate <= d, affected per Trivy status
  x1 cvss                 : max base score over active CVEs with rho > 0 (nvd > redhat > other)
  x2 exploitability       : max EPSS_v(t) * rho_v over active CVEs (EPSS from the Monday snapshot of t)
  x3 patch_risk           : 2 any active CVE without fix, 1 all fixable, 0 none active   (contract v2)
  x4,x5,x6                : posture columns from the asset inventory (constant per asset)
  x7 threat_intelligence  : 1 if any active reachable CVE is in KEV as of t, else 0     (ti_mode="kev_any")
  reachability_level      : max rho over active CVEs (enum A-01), default_rho if none
  version_range_status    : INSUFFICIENT if any active CVE has unknown status, else AFFECTED/NOT_IN
  y                       : 100 * mean over tau in {t+7,...,t+28} of max_v X_v(tau)*S_{v,a}(tau),
                            X_v = max(EPSS_v(tau), 1[v in KEV as of tau]); S = 1[v active at tau]
                            (S = rho_v by default, LabelSpec.s_uses_rho=False gives S = 1). null if any tau
                            lies beyond the last sealed snapshot (feature-only row).

Everything reads through snapshots.verify_manifest(); a missing week raises.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from . import snapshots as S
except ImportError:  # imported as a bare module with python_hanfis/ on sys.path (test/ convention)
    import snapshots as S  # type: ignore

RHO_LEVELS = (0.0, 0.1, 0.25, 0.6, 1.0)
CVSS_SOURCE_ORDER = ("nvd", "redhat", "ghsa", "bitnami", "ubuntu", "julia")
AFFECTED_STATUSES = {"affected", "fixed", "will_not_fix", "fix_deferred", "end_of_life"}
NOT_AFFECTED_STATUSES = {"not_affected"}
_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$")


class AssetWeekError(RuntimeError):
    pass


# ----------------------------------------------------------------------------- evidence
@dataclass(frozen=True)
class Cve:
    id: str
    pkg: str
    installed: str
    fixed: str | None
    status: str                 # trivy status, lower-case
    published: dt.date
    cvss: float | None
    cvss_source: str | None
    data_source: str | None

    @property
    def version_range_status(self) -> str:
        if self.status in AFFECTED_STATUSES:
            return "AFFECTED_VERSION_RANGE"
        if self.status in NOT_AFFECTED_STATUSES:
            return "NOT_IN_AFFECTED_VERSION_RANGE"
        return "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class ScanBundle:
    path: Path
    sha256: str
    artifact_name: str
    created_at: dt.datetime
    os_family: str
    os_version: str
    cves: tuple[Cve, ...]


def _pick_cvss(cvss: dict) -> tuple[float | None, str | None]:
    for src in CVSS_SOURCE_ORDER + tuple(sorted(k for k in cvss if k not in CVSS_SOURCE_ORDER)):
        entry = cvss.get(src) or {}
        for key in ("V4Score", "V3Score", "V2Score"):
            if isinstance(entry.get(key), (int, float)):
                return float(entry[key]), f"{src}.{key}"
    return None, None


def load_trivy_scan(path: Path) -> ScanBundle:
    raw = path.read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    if "Results" not in doc or "ArtifactName" not in doc:
        raise AssetWeekError(f"{path}: not a Trivy JSON report")
    if "@sha256:" not in doc["ArtifactName"]:
        raise AssetWeekError(f"{path}: ArtifactName is not digest-pinned: {doc['ArtifactName']}")
    cves: list[Cve] = []
    seen: set[tuple[str, str]] = set()
    for res in doc["Results"]:
        for v in res.get("Vulnerabilities") or []:
            vid = v.get("VulnerabilityID", "")
            if not _CVE_RE.match(vid):
                continue  # non-CVE advisories (GHSA-only, TEMP-) have no EPSS/KEV identity
            key = (vid, v.get("PkgID", v.get("PkgName", "")))
            if key in seen:
                continue
            seen.add(key)
            pub = v.get("PublishedDate")
            if not pub:
                raise AssetWeekError(f"{path}: {vid} lacks PublishedDate; temporal gating impossible (fail-closed)")
            score, src = _pick_cvss(v.get("CVSS") or {})
            cves.append(Cve(vid, v.get("PkgName", ""), v.get("InstalledVersion", ""), v.get("FixedVersion") or None,
                            str(v.get("Status", "unknown")).lower(), dt.date.fromisoformat(pub[:10]),
                            score, src, (v.get("DataSource") or {}).get("ID")))
    md = doc.get("Metadata", {}).get("OS", {}) or {}
    return ScanBundle(path, hashlib.sha256(raw).hexdigest(), doc["ArtifactName"],
                      dt.datetime.fromisoformat(doc["CreatedAt"][:19]).replace(tzinfo=dt.timezone.utc),
                      md.get("Family", ""), md.get("Name", ""), tuple(cves))


# ----------------------------------------------------------------------------- inventory
@dataclass(frozen=True)
class Asset:
    asset_id: str
    image_id: str
    scan_path: Path
    mfa_risk: float
    kubernetes_exposure: float
    asset_criticality: float
    default_rho: float
    package_rho: dict = field(default_factory=dict)   # {pkg_name: rho}
    protocol: str | None = None

    def rho_for(self, cve: Cve) -> float:
        return float(self.package_rho.get(cve.pkg, self.default_rho))


ASSET_COLUMNS = ("asset_id", "image_id", "scan_json", "mfa_risk", "kubernetes_exposure",
                 "asset_criticality", "default_rho", "package_rho_json", "protocol")


def load_assets(path: Path, repo_root: Path) -> list[Asset]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = set(ASSET_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise AssetWeekError(f"{path}: missing columns {sorted(missing)}")
        out, ids = [], set()
        for i, r in enumerate(reader, 2):
            if r["asset_id"] in ids:
                raise AssetWeekError(f"{path}:{i}: duplicate asset_id {r['asset_id']}")
            ids.add(r["asset_id"])
            rho = float(r["default_rho"])
            pk = json.loads(r["package_rho_json"] or "{}")
            for lvl in (rho, *pk.values()):
                if float(lvl) not in RHO_LEVELS:
                    raise AssetWeekError(f"{path}:{i}: rho {lvl} not in A-01 levels {RHO_LEVELS}")
            out.append(Asset(r["asset_id"], r["image_id"], (repo_root / r["scan_json"]).resolve(),
                             float(r["mfa_risk"]), float(r["kubernetes_exposure"]), float(r["asset_criticality"]),
                             rho, {k: float(v) for k, v in pk.items()}, r.get("protocol") or None))
    return out


# ----------------------------------------------------------------------------- snapshots
class SnapshotStore:
    """Verified, lazily-cached access to sealed snapshots."""

    def __init__(self, root: Path):
        self.root = root
        self.manifest = S.verify_manifest(root)
        self._epss: dict[dt.date, dict[str, float]] = {}
        kev_keys = sorted(self.manifest["kev"])
        if not kev_keys:
            raise AssetWeekError("no KEV snapshot in manifest")
        raw = (root / self.manifest["kev"][kev_keys[-1]]["file"]).read_bytes()
        self.kev_version, self._kev_entries = S.parse_kev_json(raw)
        self._kev_cache: dict[dt.date, set[str]] = {}

    @property
    def epss_dates(self) -> list[dt.date]:
        return sorted(dt.date.fromisoformat(k) for k in self.manifest["epss"])

    def has_epss(self, d: dt.date) -> bool:
        return d.isoformat() in self.manifest["epss"]

    def epss(self, d: dt.date) -> dict[str, float]:
        if d not in self._epss:
            rec = self.manifest["epss"].get(d.isoformat())
            if rec is None:
                raise AssetWeekError(f"EPSS snapshot for {d} not in manifest (fail-closed)")
            with gzip.open(self.root / rec["file"], "rt", encoding="utf-8") as fh:
                rows = csv.reader(l for l in fh if not l.startswith("#"))
                next(rows)
                self._epss[d] = {r[0]: float(r[1]) for r in rows if r}
        return self._epss[d]

    def epss_model_version(self, d: dt.date) -> str:
        return self.manifest["epss"][d.isoformat()]["model_version"]

    def kev_as_of(self, d: dt.date) -> set[str]:
        if d not in self._kev_cache:
            self._kev_cache[d] = S.kev_as_of(self._kev_entries, d)
        return self._kev_cache[d]


# ----------------------------------------------------------------------------- rows
@dataclass(frozen=True)
class LabelSpec:
    horizon_days: int = 30
    stride_days: int = 7
    kev_weight: float = 1.0        # X_v = max(EPSS, kev_weight * 1[KEV])
    s_uses_rho: bool = True        # S_{v,a} = rho_v (A-11: label variance must follow reachability); False -> 1
    ti_mode: str = "kev_any"       # x7 definition

    def taus(self, t: dt.date) -> list[dt.date]:
        return [t + dt.timedelta(days=k) for k in range(self.stride_days, self.horizon_days + 1, self.stride_days)]


def active_cves(scan: ScanBundle, d: dt.date) -> list[Cve]:
    return [c for c in scan.cves if c.published <= d]


def _enum_rho(x: float) -> float:
    return min(RHO_LEVELS, key=lambda lvl: abs(lvl - x))


def event_id_for(asset_id: str, week: dt.date) -> str:
    iso = week.isocalendar()
    return f"{asset_id}__{iso[0]}-W{iso[1]:02d}"


def build_row(asset: Asset, scan: ScanBundle, store: SnapshotStore, week: dt.date, spec: LabelSpec) -> dict:
    if week.weekday() != 0:
        raise AssetWeekError(f"{week} is not a Monday")
    act = active_cves(scan, week)
    affected = [c for c in act if c.version_range_status == "AFFECTED_VERSION_RANGE"]
    reach = [c for c in affected if asset.rho_for(c) > 0]
    epss_t = store.epss(week)
    kev_t = store.kev_as_of(week)

    if any(c.version_range_status == "INSUFFICIENT_EVIDENCE" for c in act):
        vrs = "INSUFFICIENT_EVIDENCE"
    elif affected:
        vrs = "AFFECTED_VERSION_RANGE"
    else:
        vrs = "NOT_IN_AFFECTED_VERSION_RANGE"

    scored = [c.cvss for c in reach if c.cvss is not None]
    cvss = (max(scored) if scored else None) if reach else 0.0
    x2 = max((epss_t[c.id] * asset.rho_for(c) for c in reach if c.id in epss_t), default=0.0)
    patch = 2.0 if any(c.fixed is None for c in affected) else (1.0 if affected else 0.0)
    if spec.ti_mode != "kev_any":
        raise AssetWeekError(f"unknown ti_mode {spec.ti_mode}")
    x7 = 1.0 if any(c.id in kev_t for c in reach) else 0.0
    rho_row = _enum_rho(max((asset.rho_for(c) for c in affected), default=asset.default_rho))

    # label
    y: float | None
    taus = spec.taus(week)
    if all(store.has_epss(tau) for tau in taus):
        vals = []
        for tau in taus:
            e, k = store.epss(tau), store.kev_as_of(tau)
            best = 0.0
            for c in active_cves(scan, tau):
                if c.version_range_status != "AFFECTED_VERSION_RANGE":
                    continue
                s = asset.rho_for(c) if spec.s_uses_rho else 1.0
                x = max(e.get(c.id, 0.0), spec.kev_weight if c.id in k else 0.0)
                best = max(best, x * s)
            vals.append(best)
        y = round(100.0 * sum(vals) / len(vals), 6)
    else:
        y = None

    return {
        "event_id": event_id_for(asset.asset_id, week),
        "image_id": asset.image_id,
        "week_start_utc": f"{week.isoformat()}T00:00:00Z",
        "cvss": cvss,
        "exploitability": round(x2, 6),
        "patch_risk": patch,
        "mfa_risk": asset.mfa_risk,
        "kubernetes_exposure": asset.kubernetes_exposure,
        "asset_criticality": asset.asset_criticality,
        "threat_intelligence": x7,
        "reachability_level": rho_row,
        "version_range_status": vrs,
        "y": y,
        "evidence_sha256": scan.sha256,
        "protocol": asset.protocol,
    }


DIAG_COLUMNS = ("n_cves_active", "n_cves_reachable", "n_kev_active", "epss_model_version")


def build_rows(assets: Iterable[Asset], store: SnapshotStore, weeks: Iterable[dt.date], spec: LabelSpec,
               with_diagnostics: bool = True) -> tuple[list[dict], list[dict]]:
    rows, diags = [], []
    for asset in assets:
        if not asset.scan_path.exists():
            raise AssetWeekError(f"{asset.asset_id}: scan bundle missing {asset.scan_path} (scan it first)")
        scan = load_trivy_scan(asset.scan_path)
        for w in weeks:
            rows.append(build_row(asset, scan, store, w, spec))
            if with_diagnostics:
                act = active_cves(scan, w)
                diags.append({"event_id": rows[-1]["event_id"],
                              "n_cves_active": len(act),
                              "n_cves_reachable": sum(asset.rho_for(c) > 0 for c in act),
                              "n_kev_active": sum(c.id in store.kev_as_of(w) for c in act),
                              "epss_model_version": store.epss_model_version(w)})
    return rows, diags


# ----------------------------------------------------------------------------- contract validation (no jsonschema dependency)
def validate_contract(rows: list[dict], schema: dict) -> list[str]:
    props, req = schema["properties"], set(schema["required"])
    problems: list[str] = []
    ids: set[str] = set()
    for r in rows:
        eid = r.get("event_id", "?")
        if eid in ids:
            problems.append(f"{eid}: duplicate event_id")
        ids.add(eid)
        if missing := req - set(r):
            problems.append(f"{eid}: missing {sorted(missing)}")
        if extra := set(r) - set(props):
            problems.append(f"{eid}: unexpected {sorted(extra)}")
        for k, v in r.items():
            p = props.get(k)
            if p is None:
                continue
            types = p["type"] if isinstance(p["type"], list) else [p["type"]]
            if v is None:
                if "null" not in types:
                    problems.append(f"{eid}.{k}: null not allowed")
                continue
            if "number" in types and not isinstance(v, (int, float)):
                problems.append(f"{eid}.{k}: not a number ({v!r})")
                continue
            if "string" in types and "number" not in types and not isinstance(v, str):
                problems.append(f"{eid}.{k}: not a string")
                continue
            if isinstance(v, (int, float)):
                if "minimum" in p and v < p["minimum"] or "maximum" in p and v > p["maximum"]:
                    problems.append(f"{eid}.{k}: {v} outside [{p.get('minimum')},{p.get('maximum')}]")
            if "enum" in p and v not in p["enum"]:
                problems.append(f"{eid}.{k}: {v!r} not in enum")
            if "pattern" in p and isinstance(v, str) and not re.match(p["pattern"], v):
                problems.append(f"{eid}.{k}: pattern mismatch")
    return problems


# ----------------------------------------------------------------------------- gate (§9)
def gate_status(rows: list[dict], min_rows: int = 1320, min_non_na: float = 0.25,
                min_positive: float = 0.25) -> dict:   # §9: >=10 obs/parameter -> >=1,320 rows
    n = len(rows)
    ys = [r["y"] for r in rows if r["y"] is not None]
    non_na = len(ys) / n if n else 0.0
    positive = sum(y > 0 for y in ys) / len(ys) if ys else 0.0
    insufficient = sum(r["version_range_status"] == "INSUFFICIENT_EVIDENCE" for r in rows)
    checks = {
        f"rows>={min_rows}": n >= min_rows,
        f"non_na>={min_non_na}": non_na >= min_non_na,
        f"positive>={min_positive}": positive >= min_positive,
        "no_INSUFFICIENT_EVIDENCE": insufficient == 0,
    }
    return {"n_rows_event_id": n, "n_assets": len({r["image_id"] for r in rows}),
            "share_non_na": round(non_na, 4), "share_positive": round(positive, 4),
            "n_insufficient": insufficient, "checks": checks,
            "TRAINING_AUTHORIZED": all(checks.values())}
