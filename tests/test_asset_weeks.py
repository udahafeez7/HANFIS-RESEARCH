"""Patch 0024: asset-week rows (contract v2) from Trivy evidence + sealed snapshots. Fully offline."""
import datetime as dt
import gzip
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from python_hanfis import asset_weeks as AW
from python_hanfis import snapshots as S

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "configs" / "anfis_source_schema_v2.json").read_text(encoding="utf-8"))
IMG = "docker.io/example/app@sha256:" + "ab" * 32
MONDAYS = S.monday_grid(dt.date(2026, 1, 5), dt.date(2026, 3, 2))          # 9 Mondays

CVES = [  # id, pkg, fixed, status, published, cvss
    ("CVE-2025-00001", "libexpat", "2.7.1-r0", "fixed", "2025-12-01", {"nvd": {"V3Score": 9.8}}),
    ("CVE-2025-00002", "busybox", None, "affected", "2026-01-20", {"redhat": {"V3Score": 5.5}}),
    ("CVE-2025-00003", "libpng", "1.6.50-r0", "fixed", "2026-02-10", {}),           # no CVSS
    ("CVE-2025-00004", "curl", "8.14.1-r2", "not_affected", "2025-06-01", {"nvd": {"V3Score": 7.5}}),
]
EPSS = {"CVE-2025-00001": 0.20, "CVE-2025-00002": 0.05, "CVE-2025-00003": 0.90, "CVE-2025-00004": 0.60}
KEV = [{"cveID": "CVE-2025-00001", "dateAdded": "2026-02-02"}]


def trivy_report(cves=CVES, status_override=None):
    vulns = []
    for vid, pkg, fixed, status, pub, cvss in cves:
        v = {"VulnerabilityID": vid, "PkgName": pkg, "PkgID": f"{pkg}@1", "InstalledVersion": "1",
             "Status": status_override.get(vid, status) if status_override else status,
             "PublishedDate": pub + "T10:00:00Z", "DataSource": {"ID": "alpine"}, "CVSS": cvss}
        if fixed:
            v["FixedVersion"] = fixed
        vulns.append(v)
    return {"SchemaVersion": 2, "CreatedAt": "2026-09-14T07:45:40Z", "ArtifactName": IMG,
            "Metadata": {"OS": {"Family": "alpine", "Name": "3.21.3"}},
            "Results": [{"Target": IMG, "Class": "os-pkgs", "Vulnerabilities": vulns}]}


def epss_gz(d):
    body = f"#model_version:v2025.03.14,score_date:{d}T00:00:00+0000\ncve,epss,percentile\n" + \
        "".join(f"{c},{s:.5f},0.5\n" for c, s in EPSS.items()) + "".join(f"CVE-2020-{i:05d},0.001,0.1\n" for i in range(50))
    return gzip.compress(body.encode())


def make_store(root: Path, mondays=MONDAYS):
    m = S.load_manifest(root)
    for d in mondays:
        raw = epss_gz(d.isoformat())
        S.record_epss(m, S.fetch_epss(d, root / "epss", opener=lambda u, raw=raw: raw, min_rows=10), root)
    kev = json.dumps({"count": len(KEV), "catalogVersion": "t", "vulnerabilities": KEV}).encode()
    S.record_kev(m, S.fetch_kev(root / "kev", opener=lambda u: kev, min_entries=1,
                                now=dt.datetime(2026, 3, 3, tzinfo=dt.timezone.utc)), root)
    S.save_manifest(root, m)
    return AW.SnapshotStore(root)


def make_asset(root: Path, report=None, **kw) -> AW.Asset:
    p = root / "scan.json"; p.write_text(json.dumps(report or trivy_report()))
    base = dict(asset_id="app-on", image_id=IMG, scan_path=p, mfa_risk=0.5, kubernetes_exposure=0.5,
                asset_criticality=3.0, default_rho=0.1, package_rho={"libexpat": 1.0}, protocol="reachability-evidence-v1")
    base.update(kw)
    return AW.Asset(**base)


class TestEvidence(unittest.TestCase):
    def test_load_and_status_mapping(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "s.json"; p.write_text(json.dumps(trivy_report()))
            scan = AW.load_trivy_scan(p)
            self.assertEqual(len(scan.cves), 4)
            by = {c.id: c for c in scan.cves}
            self.assertEqual(by["CVE-2025-00001"].version_range_status, "AFFECTED_VERSION_RANGE")
            self.assertEqual(by["CVE-2025-00004"].version_range_status, "NOT_IN_AFFECTED_VERSION_RANGE")
            self.assertEqual((by["CVE-2025-00002"].cvss, by["CVE-2025-00002"].cvss_source), (5.5, "redhat.V3Score"))
            self.assertIsNone(by["CVE-2025-00003"].cvss)

    def test_pinning_repo_digest_or_local_image_id(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "s.json"
            r = trivy_report(); p.write_text(json.dumps(r))
            self.assertEqual(AW.load_trivy_scan(p).pinned_kind, "repo_digest")
            # locally built image: tag only, identity from Metadata.ImageID
            r = trivy_report(); r["ArtifactName"] = "hanfis/p0if:1.0"
            r["Metadata"]["ImageID"] = "sha256:" + "79" * 32; r["Metadata"]["RepoDigests"] = []
            p.write_text(json.dumps(r)); b = AW.load_trivy_scan(p)
            self.assertEqual((b.pinned_kind, b.pinned_identity), ("image_id", "sha256:" + "79" * 32))
            # tag only, no ImageID -> refuse
            del r["Metadata"]["ImageID"]; p.write_text(json.dumps(r))
            with self.assertRaises(AW.AssetWeekError):
                AW.load_trivy_scan(p)

    def test_inventory_must_match_evidence_identity(self):
        with TemporaryDirectory() as td:
            root = Path(td); store = make_store(root / "snap")
            wrong = make_asset(root, image_id="docker.io/example/app@sha256:" + "cd" * 32)
            with self.assertRaises(AW.AssetWeekError):
                AW.build_rows([wrong], store, MONDAYS[:2], AW.LabelSpec())

    def test_fail_closed_on_undated(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "s.json"
            r = trivy_report(); del r["Results"][0]["Vulnerabilities"][0]["PublishedDate"]; p.write_text(json.dumps(r))
            with self.assertRaises(AW.AssetWeekError):
                AW.load_trivy_scan(p)


class TestRows(unittest.TestCase):
    def test_temporal_features_and_label(self):
        with TemporaryDirectory() as td:
            root = Path(td); store = make_store(root / "snap"); asset = make_asset(root)
            scan = AW.load_trivy_scan(asset.scan_path); spec = AW.LabelSpec()
            r0 = AW.build_row(asset, scan, store, dt.date(2026, 1, 5), spec)     # only CVE-1 published
            self.assertEqual(r0["event_id"], "app-on__2026-W02")
            self.assertEqual((r0["cvss"], r0["patch_risk"], r0["threat_intelligence"], r0["reachability_level"]), (9.8, 1.0, 0.0, 1.0))
            self.assertAlmostEqual(r0["exploitability"], 0.20 * 1.0, places=6)
            self.assertEqual(r0["version_range_status"], "AFFECTED_VERSION_RANGE")
            # label window 12 Jan..2 Feb: KEV entry lands on 2 Feb -> last tau = 1.0, others 0.20
            self.assertAlmostEqual(r0["y"], 100 * (0.2 + 0.2 + 0.2 + 1.0) / 4, places=4)   # rho(libexpat)=1
            r0b = AW.build_row(asset, scan, store, dt.date(2026, 1, 5), AW.LabelSpec(s_uses_rho=False))
            self.assertAlmostEqual(r0b["y"], r0["y"], places=4)
            low = make_asset(root, asset_id="app-off", package_rho={"libexpat": 0.25})
            r0c = AW.build_row(low, scan, store, dt.date(2026, 1, 5), spec)
            self.assertAlmostEqual(r0c["y"], 0.25 * r0["y"], places=4, msg="label must scale with rho (A-11)")
            r3 = AW.build_row(asset, scan, store, dt.date(2026, 1, 26), spec)    # CVE-2 (no fix, rho 0.1) now active
            self.assertEqual((r3["patch_risk"], r3["cvss"], r3["reachability_level"]), (2.0, 9.8, 1.0))
            r5 = AW.build_row(asset, scan, store, dt.date(2026, 2, 9), spec)     # KEV known at t -> x7 = 1
            self.assertEqual(r5["threat_intelligence"], 1.0)
            self.assertIsNone(r5["y"], "window beyond last snapshot must be feature-only")
            r_last = AW.build_row(asset, scan, store, dt.date(2026, 2, 2), spec)
            self.assertIsNotNone(r_last["y"])

    def test_no_active_cves_is_zero_not_null(self):
        with TemporaryDirectory() as td:
            root = Path(td); store = make_store(root / "snap"); asset = make_asset(root)
            scan = AW.load_trivy_scan(asset.scan_path)
            # week before any CVE is published: shift CVE-1 to the future
            rep = trivy_report([("CVE-2025-00001", "libexpat", "x", "fixed", "2026-06-01", {"nvd": {"V3Score": 9.8}})])
            asset2 = make_asset(root, rep, asset_id="empty")
            r = AW.build_row(asset2, AW.load_trivy_scan(asset2.scan_path), store, dt.date(2026, 1, 5), AW.LabelSpec())
            self.assertEqual((r["cvss"], r["exploitability"], r["patch_risk"], r["version_range_status"]),
                             (0.0, 0.0, 0.0, "NOT_IN_AFFECTED_VERSION_RANGE"))

    def test_insufficient_evidence_propagates(self):
        with TemporaryDirectory() as td:
            root = Path(td); store = make_store(root / "snap")
            asset = make_asset(root, trivy_report(status_override={"CVE-2025-00001": "under_investigation"}))
            r = AW.build_row(asset, AW.load_trivy_scan(asset.scan_path), store, dt.date(2026, 1, 5), AW.LabelSpec())
            self.assertEqual(r["version_range_status"], "INSUFFICIENT_EVIDENCE")

    def test_contract_and_gate(self):
        with TemporaryDirectory() as td:
            root = Path(td); store = make_store(root / "snap"); asset = make_asset(root)
            rows, diags = AW.build_rows([asset], store, MONDAYS, AW.LabelSpec())
            self.assertEqual(len(rows), 9); self.assertEqual(AW.validate_contract(rows, SCHEMA), [])
            self.assertEqual(diags[0]["epss_model_version"], "v2025.03.14")
            bad = dict(rows[0]); bad["reachability_level"] = 0.5; bad["threat_intelligence"] = 7.4
            self.assertEqual(len(AW.validate_contract([bad], SCHEMA)), 2)
            st = AW.gate_status(rows)
            self.assertFalse(st["TRAINING_AUTHORIZED"]); self.assertEqual(st["n_rows_event_id"], 9)
            self.assertEqual((st["n_asset_ids"], st["n_image_groups"]), (1, 1))
            self.assertFalse(st["checks"]["rows>=1320"])

    def test_missing_snapshot_week_fails_closed(self):
        with TemporaryDirectory() as td:
            root = Path(td); store = make_store(root / "snap"); asset = make_asset(root)
            with self.assertRaises(AW.AssetWeekError):
                AW.build_row(asset, AW.load_trivy_scan(asset.scan_path), store, dt.date(2025, 12, 29), AW.LabelSpec())
            with self.assertRaises(AW.AssetWeekError):
                AW.build_row(asset, AW.load_trivy_scan(asset.scan_path), store, dt.date(2026, 1, 6), AW.LabelSpec())


class TestInventory(unittest.TestCase):
    def test_load_assets_validates_rho_levels(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "a.csv"
            p.write_text(",".join(AW.ASSET_COLUMNS) + "\n" + f'x,{IMG},scan.json,0.5,0.5,3,0.1,"{{""libexpat"": 1.0}}",v1\n')
            a = AW.load_assets(p, Path(td))
            self.assertEqual(a[0].package_rho, {"libexpat": 1.0})
            p.write_text(",".join(AW.ASSET_COLUMNS) + "\n" + f'x,{IMG},scan.json,0.5,0.5,3,0.5,"{{}}",v1\n')
            with self.assertRaises(AW.AssetWeekError):
                AW.load_assets(p, Path(td))


if __name__ == "__main__":
    unittest.main()
