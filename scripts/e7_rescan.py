#!/usr/bin/env python3
"""E7 -- pindai ulang seluruh aset pada D2 dengan DB Trivy yang dibekukan SATU kali, lalu tulis configs/assets_v3.csv dan manifes.

  python scripts/e7_rescan.py --d2 2026-11-02 --download-db            (resmi: butuh jaringan, DB harus segar, tanpa --limit)
  python scripts/e7_rescan.py --rehearsal --limit 3                    (latihan: DB yang ada, hanya 3 target, keluaran terpisah)
  python scripts/e7_rescan.py --d2 2026-11-02 --resume                 (lanjutkan setelah kegagalan; target selesai dilewati)
  tambahkan --dry-run untuk hanya mencetak rencana.

Aturan (pelajaran A-15): satu pindaian hanya memuat CVE yang diketahui saat itu, maka SEMUA aset dipindai dengan DB yang sama. Tiap pindaian memakai scripts/scan_image_evidence.sh
(selalu --skip-db-update). Setelah tiap pindaian dicek bahwa tanggal DB tidak berubah dan bundel mencatat tanggal DB itu; ketidakcocokan menghentikan seluruh proses.
Aset buatan lokal (image_id berawalan hanfis/) dipindai lewat name:tag dan ID Docker-nya harus sama dengan digest di assets.csv. p0if-on dan p0if-off berbagi satu pindaian.
Gagal sekali dicoba ulang satu kali; gagal lagi menghentikan proses (keadaan disimpan; --resume melanjutkan). Tidak ada aset yang dilewati diam-diam."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG_OVERRIDE = {"p0-baseline": "p0", "p0if-on": "p0if", "p0if-off": "p0if"}


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def db_updated_at(cache: Path) -> str:
    md = json.loads((cache / "db" / "metadata.json").read_text(encoding="utf-8"))
    v = md.get("UpdatedAt") or md.get("updated_at")
    if not v:
        raise RuntimeError(f"{cache}/db/metadata.json tanpa UpdatedAt")
    return str(v)


def plan_targets(rows: list[dict]) -> dict:
    """slug -> {"image": argumen pindai, "assets": [asset_id...], "expect_id": ID Docker yang diharapkan atau None}"""
    t: dict = {}
    for r in rows:
        aid, img = r["asset_id"], r["image_id"]
        slug = SLUG_OVERRIDE.get(aid, aid)
        if img.startswith("hanfis/"):
            name, _, dig = img.partition("@")
            entry = t.setdefault(slug, {"image": name, "assets": [], "expect_id": dig})
            if entry["image"] != name or entry["expect_id"] != dig:
                raise ValueError(f"{slug}: baris aset berbagi slug tetapi image berbeda")
        else:
            entry = t.setdefault(slug, {"image": img, "assets": [], "expect_id": None})
            if entry["image"] != img:
                raise ValueError(f"{slug}: slug ganda dengan image berbeda")
        entry["assets"].append(aid)
    return t


def run_scan(script: Path, slug: str, image: str, cache: Path) -> tuple[int, str, str]:
    r = subprocess.run(["bash", str(script), slug, image, str(cache)], cwd=ROOT, capture_output=True, text=True, timeout=3600)
    return r.returncode, r.stdout, r.stderr


def parse_scan_json(stdout: str) -> str | None:
    for line in stdout.splitlines()[::-1]:
        if line.startswith("SCAN_JSON="):
            return line.split("=", 1)[1].strip()
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--d2"); ap.add_argument("--assets", default=str(ROOT / "configs" / "assets.csv")); ap.add_argument("--out"); ap.add_argument("--state")
    ap.add_argument("--cache", default=str(Path.home() / ".cache" / "trivy")); ap.add_argument("--scan-script", default=str(ROOT / "scripts" / "scan_image_evidence.sh"))
    ap.add_argument("--download-db", action="store_true"); ap.add_argument("--rehearsal", action="store_true"); ap.add_argument("--limit", type=int)
    ap.add_argument("--resume", action="store_true"); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args(argv)
    if a.limit and not a.rehearsal:
        print("ABORT: --limit hanya untuk --rehearsal"); return 2
    if not a.rehearsal and not a.d2:
        print("ABORT: --d2 YYYY-MM-DD wajib untuk run resmi"); return 2
    if not a.rehearsal and not (a.download_db or a.resume):
        print("ABORT: run resmi memerlukan --download-db (atau --resume setelah unduhan)"); return 2
    tag = "rehearsal" if a.rehearsal else a.d2
    out = Path(a.out) if a.out else ROOT / "configs" / ("assets_v3_rehearsal.csv" if a.rehearsal else "assets_v3.csv")
    state_p = Path(a.state) if a.state else ROOT / "data" / "evidence" / f"e7_rescan_{tag}.json"
    cache = Path(a.cache)
    with open(a.assets, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f); fields = rd.fieldnames; rows = list(rd)
    targets = plan_targets(rows)
    names = list(targets)[: a.limit] if a.limit else list(targets)
    print(f"{len(rows)} aset -> {len(targets)} target pindai; diproses {len(names)}; keluaran {out}")
    if a.dry_run:
        for n in names: print(f"  {n}: {targets[n]['image'][:80]}  aset={targets[n]['assets']}")
        return 0
    state = json.loads(state_p.read_text(encoding="utf-8")) if (a.resume and state_p.exists()) else {"tag": tag, "started_utc": now(), "done": {}}
    if not a.resume and state_p.exists():
        print(f"ABORT: {state_p} sudah ada; pakai --resume atau hapus berkasnya dengan sengaja"); return 2
    if a.download_db:
        r = subprocess.run(["trivy", "image", "--download-db-only", "--cache-dir", str(cache)], capture_output=True, text=True)
        if r.returncode:
            print("ABORT: unduh DB gagal:", (r.stderr or r.stdout)[-300:]); return 1
    upd = db_updated_at(cache)
    if not a.rehearsal:
        d2 = dt.date.fromisoformat(a.d2); u = dt.datetime.fromisoformat(upd.replace("Z", "+00:00")).date()
        if abs((u - d2).days) > 1:
            print(f"ABORT: DB tidak segar (UpdatedAt {upd}, D2 {a.d2})"); return 2
    if state.get("db_updated_at") and state["db_updated_at"] != upd:
        print(f"ABORT: DB berubah sejak awal run ({state['db_updated_at']} -> {upd})"); return 2
    state["db_updated_at"] = upd
    state["trivy_version"] = subprocess.run(["trivy", "--version"], capture_output=True, text=True).stdout.splitlines()[:1]
    print(f"DB Trivy UpdatedAt = {upd} (dibekukan untuk seluruh run)")
    for n in names:
        t = targets[n]
        if n in state["done"]:
            print(f"  lewati (selesai): {n}"); continue
        if t["expect_id"]:
            r = subprocess.run(["docker", "image", "inspect", t["image"], "--format", "{{.Id}}"], capture_output=True, text=True)
            if r.returncode or r.stdout.strip() != t["expect_id"]:
                print(f"ABORT: ID Docker {t['image']} = {r.stdout.strip() or r.stderr.strip()[:80]} != {t['expect_id']}"); return 1
        sj = None
        for attempt in (1, 2):
            rc, so, se = run_scan(Path(a.scan_script), n, t["image"], cache)
            sj = parse_scan_json(so)
            if rc == 0 and sj:
                break
            print(f"  percobaan {attempt} gagal untuk {n} (rc={rc}): {(se or so)[-160:].strip()}"); sj = None
        if not sj:
            state_p.parent.mkdir(parents=True, exist_ok=True); state_p.write_text(json.dumps(state, indent=1), encoding="utf-8")
            print(f"ABORT: {n} gagal dua kali; keadaan disimpan di {state_p}; perbaiki lalu jalankan ulang dengan --resume"); return 1
        if db_updated_at(cache) != upd:
            print("ABORT: DB berubah selama pindaian"); return 1
        vd = ROOT / Path(sj).parent / "trivy_version_and_db.txt"
        if not vd.exists() or upd[:10] not in vd.read_text(encoding="utf-8", errors="replace"):
            print(f"ABORT: bundel {sj} tidak mencatat tanggal DB {upd[:10]}"); return 1
        state["done"][n] = {"image": t["image"], "assets": t["assets"], "scan_json": sj, "finished_utc": now()}
        state_p.parent.mkdir(parents=True, exist_ok=True); state_p.write_text(json.dumps(state, indent=1), encoding="utf-8")
        print(f"  selesai: {n} -> {sj}")
    amap = {aid: st["scan_json"] for st in state["done"].values() for aid in st["assets"]}
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for r in rows:
            r = dict(r); r["scan_json"] = amap.get(r["asset_id"], r["scan_json"]); w.writerow(r)
    state["finished_utc"] = now(); state["assets_out"] = str(out); state["assets_out_sha256"] = sha256_file(out)
    state["n_targets_done"] = len(state["done"]); state["n_assets_updated"] = len(amap); state_p.write_text(json.dumps(state, indent=1), encoding="utf-8")
    complete = len(state["done"]) == len(targets)
    print(f"ditulis: {out} ({len(amap)} dari {len(rows)} aset diperbarui)\nSTATUS=E7_RESCAN_{'DONE' if complete and not a.rehearsal else 'REHEARSAL_DONE' if a.rehearsal else 'PARTIAL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
