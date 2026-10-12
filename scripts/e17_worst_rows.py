#!/usr/bin/env python
"""E17 -- penjelasan per baris untuk galat terbesar (POST HOC, deskriptif; tanpa pelatihan). Analogi 'prediction explanation dengan ambang' pada model hosting: hanya baris dengan galat ekstrem yang dijelaskan.
Untuk tiap metode (persistence, rumus, HANFIS) dicetak N baris dengan galat kuadrat terbesar: aset, minggu, fold, label, ketiga prediksi, x2, perubahan x2 selama --lag-weeks minggu, x7 (KEV), perubahan x7, dan porsi galat total; lalu aset yang paling sering muncul.
Tujuannya mengetahui PERISTIWA apa yang membuat galat terkonsentrasi (E16).   python scripts/e17_worst_rows.py [--pred GLOB --table CSV --top 12 --lag-weeks 4]"""
import argparse, glob, sys
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--pred", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv")
ap.add_argument("--top", type=int, default=12); ap.add_argument("--lag-weeks", type=int, default=4); a = ap.parse_args()
fs = sorted(glob.glob(a.pred))
if not fs: sys.exit(f"ABORT: tidak ada berkas prediksi: {a.pred}")
P = pd.read_csv(fs[-1]); T = pd.read_csv(a.table, usecols=["event_id", "week_start_utc", "exploitability", "threat_intelligence"]); print(f"prediksi: {fs[-1]} | {len(P)} baris | jendela perubahan {a.lag_weeks} minggu")
T["asset"] = T["event_id"].str.rsplit("__", n=1).str[0]; T["w"] = pd.to_datetime(T["week_start_utc"], utc=True).dt.tz_localize(None).dt.normalize()
prev = T[["asset", "w", "exploitability", "threat_intelligence"]].copy(); prev["w"] = prev["w"] + pd.Timedelta(a.lag_weeks * 7, unit="D"); prev = prev.rename(columns={"exploitability": "x2p", "threat_intelligence": "x7p"})
D = P.merge(T[["event_id", "asset", "w", "exploitability", "threat_intelligence"]], on="event_id", how="left").merge(prev, on=["asset", "w"], how="left")
D["dx2"] = D["exploitability"] - D["x2p"]; D["dx7"] = D["threat_intelligence"] - D["x7p"]; M = {"persistence": "y_pers", "rumus": "y_maxform", "HANFIS": "y_full"}
for m, c in M.items(): D["e_" + m] = (D[c] - D["y_true"]) ** 2
for m in M:
    tot = D["e_" + m].sum(); W = D.sort_values("e_" + m, ascending=False).head(a.top); top1 = D.sort_values("e_" + m, ascending=False).head(max(1, len(D) // 100))
    chg = ((top1["dx2"].abs() > 1e-12) | (top1["dx7"].abs() > 1e-12)).mean()
    print(f"\n== {m}: {a.top} baris dengan galat kuadrat terbesar (total {W['e_' + m].sum() / tot:.1%} dari SSE; 1% terburuk: {top1['e_' + m].sum() / tot:.1%} SSE, {chg:.0%} di antaranya dengan perubahan masukan) ==")
    print(f"{'aset':26} {'minggu':>8} {'f':>1} {'y':>7} {'pers':>7} {'rumus':>7} {'HANFIS':>7} {'x2':>6} {'dx2':>6} {'x7':>3} {'dx7':>4}")
    for _, r in W.iterrows(): print(f"{r['asset'][:26]:26} {str(r['event_id']).rsplit('__', 1)[1][-8:]:>8} {int(r['fold']) if 'fold' in D else 0:1d} {r['y_true']:7.2f} {r['y_pers']:7.2f} {r['y_maxform']:7.2f} {r['y_full']:7.2f} {r['exploitability']:6.3f} {r['dx2']:+6.3f} {r['threat_intelligence']:3.0f} {r['dx7']:+4.0f}")
    g = D.groupby("asset")["e_" + m].sum().sort_values(ascending=False).head(6); print("   aset dengan SSE terbesar: " + "; ".join(f"{k} {v / tot:.1%}" for k, v in g.items()))
print("\nSTATUS=E17_DONE (deskriptif, post hoc)")
