#!/usr/bin/env python3
"""ANALISIS EKSPLORATORI (bukan bagian praregistrasi E4; tidak mengubah hasil konfirmatori). Hanya MEMBACA predictions_*.csv.
1) reproduksi SS vs persistence/ridge/CVSS (cek terhadap e4_analyse.py); 2) pengaruh per image; 3) robustness (leave-one-image-out,
buang k image terburuk); 4) metrik peringkat per (fold, minggu): Spearman dan presisi@20%.
Jalankan dari akar repo:  python scripts/e4_influence.py --predictions results_python/e4bis_120/predictions_20261002T103905Z.csv"""
import argparse, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd

MODELS = {"hanfis": "y_hanfis", "persistence": "y_persistence", "ridge7": "y_ridge_7inputs", "cvss": "y_cvss_only",
          "matched": "y_matched", "flat_full": "y_flat_full"}

def load(path):
    d = pd.read_csv(path)
    need = ["event_id", "image_id", "fold", "y_true"] + list(MODELS.values())
    miss = [c for c in need if c not in d.columns]
    if miss: sys.exit(f"ABORT: kolom hilang: {miss}")
    n0 = len(d); d = d.dropna(subset=["y_true"] + list(MODELS.values())).copy()
    d["asset"] = d["event_id"].str.rsplit("__", n=1).str[0]; d["week"] = d["event_id"].str.rsplit("__", n=1).str[1]
    for k, c in MODELS.items(): d["sq_" + k] = (d["y_true"] - d[c]) ** 2
    print(f"baris: {n0} -> {len(d)} (setelah membuang NaN); image: {d['image_id'].nunique()}; aset: {d['asset'].nunique()}; fold: {sorted(int(x) for x in d['fold'].unique())}")
    return d

def ss(sq_h, sq_ref): return 1.0 - sq_h / sq_ref

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", required=True); ap.add_argument("--out-dir", default="results_python/e4_influence")
    ap.add_argument("--n-boot", type=int, default=2000); ap.add_argument("--seed", type=int, default=20261006)
    ap.add_argument("--min-rank-n", type=int, default=8); a = ap.parse_args(argv)
    d = load(a.predictions); out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    print("\n== 1. SS (poolled) HANFIS terhadap pembanding: SS = 1 - SSE_hanfis / SSE_ref ==")
    rows = []
    for ref in ("persistence", "ridge7", "cvss", "matched", "flat_full"):
        pooled = ss(d.sq_hanfis.sum(), d["sq_" + ref].sum())
        per_fold = [ss(g.sq_hanfis.sum(), g["sq_" + ref].sum()) for _, g in d.groupby("fold")]
        rows.append(dict(ref=ref, ss_pooled=pooled, ss_mean_of_folds=np.mean(per_fold)))
    s1 = pd.DataFrame(rows); print(s1.round(4).to_string(index=False)); s1.to_csv(out / "ss_reproduction.csv", index=False)
    print("  (bandingkan baris persistence dengan 0.0146 pada E4 penuh; bila jauh berbeda, definisi statistik e4_analyse.py berbeda dari ini)")
    # per image
    g = d.groupby("image_id").agg(n=("y_true", "size"), sq_h=("sq_hanfis", "sum"), sq_p=("sq_persistence", "sum"),
                                  sq_r=("sq_ridge7", "sum"), y_mean=("y_true", "mean"), y_max=("y_true", "max")).reset_index()
    g["delta_vs_pers"] = g.sq_p - g.sq_h          # > 0: HANFIS lebih baik dari persistence pada image ini
    g["share_of_hanfis_sse"] = g.sq_h / g.sq_h.sum()
    g = g.sort_values("delta_vs_pers"); g.to_csv(out / "per_image.csv", index=False)
    print("\n== 2. Image yang paling merugikan HANFIS dibanding persistence (delta = SSE_pers - SSE_hanfis, negatif = HANFIS lebih buruk) ==")
    cols = ["image_id", "n", "y_mean", "y_max", "delta_vs_pers", "share_of_hanfis_sse"]
    t = g.head(8)[cols].copy(); t["image_id"] = t["image_id"].str.slice(0, 48); print(t.round(3).to_string(index=False))
    print("\n   image yang paling menguntungkan HANFIS:")
    t = g.tail(5)[cols].copy(); t["image_id"] = t["image_id"].str.slice(0, 48); print(t.round(3).to_string(index=False))
    top5 = g.sort_values("sq_h", ascending=False).head(5).sq_h.sum() / g.sq_h.sum()
    print(f"\n   5 image dengan SSE HANFIS terbesar menyumbang {top5:.1%} dari total SSE HANFIS (dari {len(g)} image)")
    # robustness
    print("\n== 3. Robustness SS vs persistence ==")
    tot_h, tot_p = g.sq_h.sum(), g.sq_p.sum(); base = ss(tot_h, tot_p)
    loio = [ss(tot_h - r.sq_h, tot_p - r.sq_p) for r in g.itertuples()]
    print(f"   pooled {base:.4f}; leave-one-image-out: min {min(loio):.4f}, maks {max(loio):.4f}")
    worst = g.sort_values("delta_vs_pers")  # paling negatif dulu
    for k in (1, 3, 5, 10):
        w = worst.head(k); print(f"   buang {k:>2} image terburuk -> SS {ss(tot_h - w.sq_h.sum(), tot_p - w.sq_p.sum()):.4f}")
    rng = np.random.default_rng(a.seed); n = len(g); sh, sp = g.sq_h.values, g.sq_p.values
    bs = np.empty(a.n_boot)
    for b in range(a.n_boot):
        ix = rng.integers(0, n, n); bs[b] = 1 - sh[ix].sum() / sp[ix].sum()
    lo, hi = np.percentile(bs, [2.5, 97.5]); print(f"   bootstrap image-clustered ({a.n_boot}x): SS pooled {base:.4f}, CI95 [{lo:.3f}, {hi:.3f}]  (E4 penuh: [-0.607, 0.246])")
    # ranking
    print(f"\n== 4. Peringkat per (fold, minggu), minimal {a.min_rank_n} image per kelompok ==")
    res = {k: [] for k in ("hanfis", "persistence", "ridge7", "cvss")}; prec = {k: [] for k in res}; ng = 0
    warnings.simplefilter("ignore", RuntimeWarning)
    for (_, _), gg in d.groupby(["fold", "week"]):
        gg = gg.drop_duplicates("image_id")
        if len(gg) < a.min_rank_n: continue
        ng += 1; kk = max(1, int(round(0.2 * len(gg)))); true_top = set(gg.nlargest(kk, "y_true").image_id)
        for k in res:
            p = gg[MODELS[k]]
            res[k].append(p.rank().corr(gg.y_true.rank()))
            prec[k].append(len(set(gg.assign(p=p).nlargest(kk, "p").image_id) & true_top) / kk)
    def nm(v):
        v = [x for x in v if x == x]
        return float(np.mean(v)) if v else float("nan")
    r = pd.DataFrame({"spearman_mean": {k: nm(v) for k, v in res.items()}, "precision_at_20pct": {k: nm(v) for k, v in prec.items()}})
    print(f"   {ng} kelompok (fold x minggu)"); print(r.round(3).to_string()); r.to_csv(out / "ranking.csv")
    print(f"\nKeluaran: {out}/ (ss_reproduction.csv, per_image.csv, ranking.csv). EKSPLORATORI, post hoc.")
    return 0
if __name__ == "__main__": sys.exit(main())
