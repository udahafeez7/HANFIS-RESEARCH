"""Patch 0023: sealed EPSS/KEV snapshots — offline tests via injected opener."""
import datetime as dt
import gzip
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from python_hanfis import snapshots as S


def epss_bytes(date: str, rows: int, model="v2025.03.14", header_date=None, bad_row=None) -> bytes:
    lines = [f"#model_version:{model},score_date:{header_date or date}T00:00:00+0000", "cve,epss,percentile"]
    for i in range(rows):
        lines.append(f"CVE-2024-{i:05d},{(i % 1000) / 1000:.5f},{(i % 1000) / 1000:.5f}")
    if bad_row:
        lines.append(bad_row)
    return gzip.compress("\n".join(lines).encode("utf-8"))


def kev_bytes(entries):
    doc = {"title": "CISA KEV", "catalogVersion": "2026.09.28", "count": len(entries), "vulnerabilities": entries}
    return json.dumps(doc).encode("utf-8")


KEV = [{"cveID": "CVE-2021-44228", "dateAdded": "2021-12-10"}, {"cveID": "CVE-2024-3400", "dateAdded": "2024-04-12"},
       {"cveID": "CVE-2026-0001", "dateAdded": "2026-09-15"}]


class TestGrid(unittest.TestCase):
    def test_monday_grid_snaps_to_mondays_inclusive(self):
        g = S.monday_grid(dt.date(2025, 9, 1), dt.date(2026, 9, 21))
        self.assertEqual(g[0], dt.date(2025, 9, 1)); self.assertEqual(g[-1], dt.date(2026, 9, 21))
        self.assertEqual(len(g), 56); self.assertTrue(all(d.weekday() == 0 for d in g))
        self.assertEqual(S.monday_grid(dt.date(2026, 9, 29), dt.date(2026, 10, 6))[0], dt.date(2026, 10, 5))
        with self.assertRaises(S.SnapshotError):
            S.monday_grid(dt.date(2026, 2, 1), dt.date(2026, 1, 1))


class TestEpss(unittest.TestCase):
    def test_parse_ok(self):
        model, n = S.parse_epss_gz(epss_bytes("2026-09-21", 50), dt.date(2026, 9, 21))
        self.assertEqual((model, n), ("v2025.03.14", 50))

    def test_fail_closed(self):
        d = dt.date(2026, 9, 21)
        cases = {
            "wrong date": epss_bytes("2026-09-21", 5, header_date="2026-09-14"),
            "not gzip": b"cve,epss,percentile\n",
            "bad cve": epss_bytes("2026-09-21", 5, bad_row="NOTACVE,0.1,0.1"),
            "score>1": epss_bytes("2026-09-21", 5, bad_row="CVE-2024-99999,1.5,0.9"),
            "no header": gzip.compress(b"cve,epss,percentile\nCVE-2024-1,0.1,0.1\n"),
        }
        for name, raw in cases.items():
            with self.subTest(name), self.assertRaises(S.SnapshotError):
                S.parse_epss_gz(raw, d)

    def test_fetch_refuses_truncated_and_seals_good(self):
        d = dt.date(2026, 9, 21)
        with TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(S.SnapshotError):
                S.fetch_epss(d, root / "epss", opener=lambda u: epss_bytes("2026-09-21", 10), min_rows=100)
            self.assertFalse((root / "epss" / "epss_scores-2026-09-21.csv.gz").exists(), "nothing written on failure")
            raw = epss_bytes("2026-09-21", 120)
            snap = S.fetch_epss(d, root / "epss", opener=lambda u: raw, min_rows=100)
            self.assertEqual(snap.path.read_bytes(), raw); self.assertEqual(snap.sha256, S.sha256_bytes(raw))
            df = S.load_epss(snap.path)
            self.assertEqual(list(df.columns), ["cve", "epss", "percentile"]); self.assertEqual(len(df), 120)


class TestKev(unittest.TestCase):
    def test_as_of_reconstruction(self):
        _, entries = S.parse_kev_json(kev_bytes(KEV))
        self.assertEqual(S.kev_as_of(entries, dt.date(2024, 4, 11)), {"CVE-2021-44228"})
        self.assertEqual(S.kev_as_of(entries, dt.date(2024, 4, 12)), {"CVE-2021-44228", "CVE-2024-3400"})
        self.assertEqual(len(S.kev_as_of(entries, dt.date(2026, 9, 21))), 3)

    def test_fail_closed(self):
        with self.assertRaises(S.SnapshotError):
            S.parse_kev_json(b"{not json")
        bad = json.loads(kev_bytes(KEV)); bad["count"] = 99
        with self.assertRaises(S.SnapshotError):
            S.parse_kev_json(json.dumps(bad).encode())
        with TemporaryDirectory() as td:
            with self.assertRaises(S.SnapshotError):
                S.fetch_kev(Path(td), opener=lambda u: kev_bytes(KEV), min_entries=10)


class TestManifest(unittest.TestCase):
    def test_seal_verify_tamper(self):
        start, end = dt.date(2026, 9, 7), dt.date(2026, 9, 21)
        with TemporaryDirectory() as td:
            root = Path(td); m = S.load_manifest(root)
            for d in S.monday_grid(start, end):
                raw = epss_bytes(d.isoformat(), 30)
                S.record_epss(m, S.fetch_epss(d, root / "epss", opener=lambda u, raw=raw: raw, min_rows=10), root)
            S.record_kev(m, S.fetch_kev(root / "kev", opener=lambda u: kev_bytes(KEV), min_entries=1,
                                        now=dt.datetime(2026, 9, 28, tzinfo=dt.timezone.utc)), root)
            S.save_manifest(root, m)
            st = S.status(root, start, end)
            self.assertEqual((st["weeks_expected"], st["weeks_present"], st["sealed"]), (3, 3, True))
            st2 = S.status(root, start, dt.date(2026, 9, 28))
            self.assertEqual(st2["weeks_missing"], ["2026-09-28"]); self.assertFalse(st2["sealed"])
            # tamper one byte -> verification must fail
            p = root / "epss" / "epss_scores-2026-09-14.csv.gz"
            b = bytearray(p.read_bytes()); b[-1] ^= 0xFF; p.write_bytes(bytes(b))
            with self.assertRaises(S.SnapshotError):
                S.verify_manifest(root)
            p.unlink()
            with self.assertRaises(S.SnapshotError):
                S.verify_manifest(root)


if __name__ == "__main__":
    unittest.main()
