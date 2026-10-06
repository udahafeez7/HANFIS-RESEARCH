#!/usr/bin/env python3
"""ANALISIS EKSPLORATORI (post hoc; bukan praregistrasi E4; tidak mengubah hasil konfirmatori). Hanya MEMBACA predictions_*.csv.
A) SS leave-one-fold-out terhadap tiap pembanding (apakah satu fold mendominasi?);
B) SS di DALAM vs LUAR jendela ketidakcocokan label setelah pergantian model EPSS (2026-06-15);
C) SSE per minggu di sekitar jendela, dan 10 minggu dengan keunggulan HANFIS-vs-persistence terbesar.
Jendela: label minggu t memakai EPSS t+7..t+28 hari; label persistence (t-28) memakai t-21..t. Model baru mulai 2026-06-15,
sehingga y(t) berbasis model baru bila t >= 2026-06-08 sedangkan label persistence masih lama sampai t <= 2026-07-06 (eksklusif)."""
import argparse, datetime as dt, sys
from pathlib import Path
import numpy as np, pandas as pd
M = {"hanfis": "y_hanfis", "persistence": "y_persistence", "ridge7": "y_ridge_7inputs", "matched": "y_matched", "flat_full": "y_flat_full"}
REFS = ["persistence", "matched", "ridge7", "flat_full"]

def week_date(w):
    y, k = w.split("-W"); return pd.Timestamp(dt.date.fromisocalendar(int(y), int(k), 1))

def ss(df, ref): return 1.0 - df["sq_hanfis"].sum() / df["sq_" + ref].sum() if len(df) else float("nan")

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--predictions", required=True)
    ap.add_argument("--out-dir", default="results_python/e4_regime")
    ap.add_argument("--window-start", default="2026-06-08"); ap.add_argument("--window-end", default="2026-07-06"); a = ap.parse_args(argv)
    d = pd.read_csv(a.predictions); cols = ["y_true"] + list(M.values()); d = d.dropna(subset=cols).copy()
    d["week"] = d["event_id"].str.rsplit("__", n=1).str[1]; d["wdate"] = d["week"].map(week_date)
    for k, c in M.items(): d["sq_" + k] = (d["y_true"] - d[c]) ** 2
    ws, we = pd.Timestamp(a.window_start), pd.Timestamp(a.window_end); d["in_win"] = (d.wdate >= ws) & (d.wdate < we)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    print(f"baris {len(d)}; jendela [{a.window_start}, {a.window_end}) berisi {int(d.in_win.sum())} baris dari {d.loc[d.in_win,'week'].nunique()} minggu")
    print("\n== A. SS pooled (semua fold) dan SS tanpa satu fold (leave-one-fold-out) ==")
    rows = [dict(buang="(tidak ada)", **{r: ss(d, r) for r in REFS})]
    for f in sorted(d.fold.unique()): rows.append(dict(buang=f"fold {int(f)}", **{r: ss(d[d.fold != f], r) for r in REFS}))
    A = pd.DataFrame(rows); print(A.round(4).to_string(index=False)); A.to_csv(out / "leave_one_fold_out.csv", index=False)
    print("\n== B. SS di dalam vs luar jendela pergantian model EPSS ==")
    B = pd.DataFrame([dict(bagian="semua", n=len(d), **{r: ss(d, r) for r in REFS}),
                      dict(bagian="di dalam jendela", n=int(d.in_win.sum()), **{r: ss(d[d.in_win], r) for r in REFS}),
                      dict(bagian="di luar jendela", n=int((~d.in_win).sum()), **{r: ss(d[~d.in_win], r) for r in REFS})])
    print(B.round(4).to_string(index=False)); B.to_csv(out / "window_split.csv", index=False)
    w = d.groupby(["week", "wdate"]).agg(n=("y_true", "size"), sse_hanfis=("sq_hanfis", "sum"), sse_pers=("sq_persistence", "sum"),
                                         sse_matched=("sq_matched", "sum"), sse_ridge7=("sq_ridge7", "sum")).reset_index().sort_values("wdate")
    w["adv_vs_pers"] = w.sse_pers - w.sse_hanfis; w["dalam_jendela"] = (w.wdate >= ws) & (w.wdate < we); w.to_csv(out / "per_week.csv", index=False)
    print("\n== C1. SSE per minggu, 3 minggu sebelum sampai 3 minggu sesudah jendela ==")
    near = w[(w.wdate >= ws - pd.Timedelta(21, unit="D")) & (w.wdate < we + pd.Timedelta(21, unit="D"))]
    print(near[["week", "n", "sse_hanfis", "sse_pers", "sse_matched", "adv_vs_pers", "dalam_jendela"]].round(1).to_string(index=False))
    print("\n== C2. 10 minggu dengan keunggulan HANFIS terhadap persistence terbesar (adv = SSE_pers - SSE_hanfis) ==")
    top = w.sort_values("adv_vs_pers", ascending=False).head(10)
    print(top[["week", "n", "sse_hanfis", "sse_pers", "adv_vs_pers", "dalam_jendela"]].round(1).to_string(index=False))
    tot = w.adv_vs_pers.sum(); print(f"\n   total keunggulan = {tot:.1f}; dari minggu di dalam jendela = {w.loc[w.dalam_jendela,'adv_vs_pers'].sum():.1f}; dari 10 minggu teratas = {top.adv_vs_pers.sum():.1f}")
    print(f"\nKeluaran: {out}/ . EKSPLORATORI, post hoc.")
    return 0
if __name__ == "__main__": sys.exit(main())
