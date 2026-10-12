#!/usr/bin/env python3
"""Selaraskan asset_criticality di configs/assets.csv dengan nilai yang BENAR-BENAR dipakai tabel E4-bis (model E4 sampai E11 dan E7 dilatih pada nilai itu), hanya untuk baris di luar kontrak [1,5].
Per aset: nilai tabel harus tunggal dan valid, jika tidak ABORT (keputusan manual). Format berkas dipertahankan byte demi byte (hanya satu kolom pada baris itu yang diganti; CRLF dan kutipan kolom lain utuh); setelah menulis, `git diff --numstat` harus menunjukkan TEPAT satu baris berubah per aset;
jika tidak, berkas dikembalikan (git checkout) dan skrip berhenti. Dari akar repo:  python scripts/fix_assets_criticality.py [--assets configs/assets.csv] [--table data/processed/asset_weeks_v2_120assets_e4bis.csv]"""
import argparse, subprocess, sys
from pathlib import Path
import pandas as pd
ap = argparse.ArgumentParser(); ap.add_argument("--assets", default="configs/assets.csv"); ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv"); a = ap.parse_args()
A, T = Path(a.assets), Path(a.table); raw = A.read_bytes().decode("utf-8"); lines = raw.splitlines(keepends=True); head = lines[0].strip().split(",")
if head[:6] != ["asset_id", "image_id", "scan_json", "mfa_risk", "kubernetes_exposure", "asset_criticality"]: print(f"ABORT: kolom awal tidak sesuai dugaan: {head[:6]}"); sys.exit(2)
t = pd.read_csv(T, usecols=["event_id", "asset_criticality"]); t["asset"] = t["event_id"].str.rsplit("__", n=1).str[0]; g = t.groupby("asset")["asset_criticality"].agg(["min", "max"]); changes = []
for i in range(1, len(lines)):
    parts = lines[i].split(",", 6)                      # enam kolom pertama tidak memuat koma atau kutip; sisanya dibiarkan utuh
    if len(parts) < 7 or '"' in ",".join(parts[:6]): continue
    try: v = float(parts[5])
    except ValueError: continue
    if 1 <= v <= 5: continue
    k = parts[0]
    if k not in g.index or g.loc[k, "min"] != g.loc[k, "max"] or not (1 <= g.loc[k, "min"] <= 5): print(f"ABORT: {k}: tabel E4-bis tidak memberi satu nilai valid ({g.loc[k].to_dict() if k in g.index else 'aset tidak ada'}); keputusan manual"); sys.exit(2)
    new = str(int(g.loc[k, "min"])); changes.append((k, parts[5], new)); parts[5] = new; lines[i] = ",".join(parts)
if not changes: print("Tidak ada nilai di luar [1,5]; tidak ada yang diubah."); sys.exit(0)
A.write_bytes("".join(lines).encode("utf-8"))
st = subprocess.run(["git", "diff", "--numstat", "--", str(A)], capture_output=True, text=True).stdout.split()
if len(st) < 2 or int(st[0]) != len(changes) or int(st[1]) != len(changes):
    subprocess.run(["git", "checkout", "--", str(A)]); print(f"ABORT: diff tidak tepat {len(changes)} baris (git: {st[:2]}); berkas DIKEMBALIKAN, format penulisan ulang berbeda dari aslinya. Ubah manual tiga baris itu."); sys.exit(2)
print(f"OK: {len(changes)} baris diubah, format utuh:"); [print(f"  {k}: {o} -> {n}") for k, o, n in changes]
