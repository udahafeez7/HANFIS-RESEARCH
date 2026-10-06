#!/usr/bin/env python3
"""Tabel sensitivitas E4: hanya minggu yang SELURUH label-nya (t+7..t+28) memakai model EPSS lama.
Pergantian model EPSS v2025.03.14 -> v2026.06.15 pada 2026-06-15; minggu terakhir yang aman = 2026-05-11.
Hanya memfilter baris; tidak mengubah nilai. Menulis tabel + sha256. Analisis POST HOC (tidak dipraregistrasi)."""
import argparse, hashlib
import pandas as pd
ap = argparse.ArgumentParser()
ap.add_argument("--src", default="data/processed/asset_weeks_v2_120assets_e4bis.csv")
ap.add_argument("--dst", default="data/processed/asset_weeks_v2_120assets_e4bis_preEPSSchange.csv")
ap.add_argument("--last-week", default="2026-05-11")
a = ap.parse_args()
d = pd.read_csv(a.src)
d["week_start_utc"] = pd.to_datetime(d["week_start_utc"], utc=True)
k = d[d["week_start_utc"] <= pd.Timestamp(a.last_week, tz="UTC")]
k.to_csv(a.dst, index=False)
h = hashlib.sha256(open(a.dst, "rb").read()).hexdigest()
print(f"{len(d)} -> {len(k)} baris; {k['week_start_utc'].nunique()} minggu; {k['week_start_utc'].min().date()}..{k['week_start_utc'].max().date()}")
print("sha256", h)
