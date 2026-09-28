"""Patch 0029: deterministic balanced posture factorial for scan-only assets."""
import csv
import importlib.util
import json
import unittest
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("assign_posture", ROOT / "scripts" / "assign_posture.py")
AP = importlib.util.module_from_spec(spec); spec.loader.exec_module(AP)


class TestPosture(unittest.TestCase):
    def test_first_45_cover_every_cell_once_and_are_stable(self):
        cells = [AP.cell_for(i) for i in range(45)]
        self.assertEqual(len(set(cells)), 45); self.assertEqual(set(cells), set(AP.CELLS))
        self.assertEqual(cells[:3], [AP.cell_for(0), AP.cell_for(1), AP.cell_for(2)])
        self.assertEqual(Counter(c[0] for c in cells), {0.0: 15, 0.5: 15, 1.0: 15})
        self.assertEqual(Counter(c[2] for c in cells), {1: 9, 2: 9, 3: 9, 4: 9, 5: 9})
        self.assertNotEqual(AP.cell_for(0), AP.cell_for(45))        # second block reshuffled

    def test_append_is_fail_closed_and_positional(self):
        with TemporaryDirectory() as td:
            root = Path(td); scan = root / "s.json"; scan.write_text("{}")
            assets = root / "assets.csv"
            assets.write_text(",".join(AP.COLUMNS) + "\n" + "p0if-on,x@sha256:" + "a" * 64 + ",s.json,0.5,0.5,3,0.1,\"{}\",reachability-evidence-v1\n")
            AP.ROOT = root
            r1 = AP.append_asset("redis", "docker.io/library/redis@sha256:" + "b" * 64, "s.json", 0.1, "scan-only-v1", assets)
            r2 = AP.append_asset("nginx", "docker.io/library/nginx@sha256:" + "c" * 64, "s.json", 0.1, "scan-only-v1", assets)
            self.assertEqual((r1["mfa_risk"], r1["kubernetes_exposure"], r1["asset_criticality"]), AP.cell_for(0))
            self.assertEqual((r2["mfa_risk"], r2["kubernetes_exposure"], r2["asset_criticality"]), AP.cell_for(1))
            rows = list(csv.DictReader(assets.open()))
            self.assertEqual([r["asset_id"] for r in rows], ["p0if-on", "redis", "nginx"])
            self.assertEqual(json.loads(rows[1]["package_rho_json"]), {})
            with self.assertRaises(SystemExit):
                AP.append_asset("redis", "docker.io/library/redis@sha256:" + "b" * 64, "s.json", 0.1, "scan-only-v1", assets)
            with self.assertRaises(SystemExit):
                AP.append_asset("tagged", "docker.io/library/redis:7", "s.json", 0.1, "scan-only-v1", assets)


if __name__ == "__main__":
    unittest.main()
