#!/usr/bin/env python3
"""E6 -- bagian 'dilaporkan tanpa kriteria' dari praregistrasi, dijalankan SETELAH `e6_explain.py --run`. TIDAK mengubah keputusan H6-*.
(1) mereproduksi persis run tercatat (seed dan urutan undian sama) dan membandingkannya dengan JSON hasil; (2) sebaran H6c per fold, periode, kelompok, dan baris tersaturasi;
(3) H6a: berapa pasangan benar-benar naik (bukan sekadar >= 0) dan berapa yang keluarannya terjepit; (4) kontras ON-OFF model vs label pada minggu uji.
Semua keluaran bersifat DESKRIPTIF. Jalankan dari akar repo:  python scripts/e6_descriptives.py"""
import argparse, glob, json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
import e6_explain as e6

CUT = pd.Timestamp("2026-06-08")


def summ(g):
    nd = g[g["nondeg"]]
    return {"baris": int(len(g)), "degenerat": int((~g["nondeg"]).sum()), "frac_teratas_menang": float(nd["beat"].mean()) if len(nd) else float("nan"),
            "rasio": float(g["d_top"].sum() / max(g["d_rm"].sum(), 1e-300))}


def main(argv=None, adapters64=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--ndraw", type=int, default=100); ap.add_argument("--rand-seed", type=int, default=20261007); a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    meta = json.load(open(root / e6.MODELS_DIR / e6.META_FILE)); table = pd.read_csv(root / e6.TABLE); preds = pd.read_csv(root / e6.MODELS_DIR / e6.PRED_FILE)
    df, X = e6.build_inputs(table, meta)
    ads = adapters64 if adapters64 is not None else e6.load_torch_adapters(root, meta, True)
    idx = {e: i for i, e in enumerate(df["event_id"])}
    wk = pd.to_datetime(df["week_start_utc"], utc=True).dt.tz_localize(None).to_numpy()   # tanggal UTC naif; kolom bertanda zona waktu tidak dapat dibandingkan dengan np.datetime64
    rng = np.random.default_rng(a.rand_seed)
    recs = []
    for key, ad in sorted(ads.items()):
        sub = preds[preds["fold"] == key[0]]
        rows = np.array([idx[e] for e in sub["event_id"]]); Xt = X[rows]; ok = ~np.isnan(Xt).any(1); rows, Xt = rows[ok], Xt[ok]
        r = e6.h6c(ad, Xt, a.k, a.ndraw, rng)
        recs.append(pd.DataFrame({"fold": key[0], "seed": key[1], "event_id": df["event_id"].to_numpy()[rows], "asset": df["asset"].to_numpy()[rows], "week": wk[rows],
                                  "y0": ad.forward(Xt), "d_top": r["d_top"], "d_rm": r["d_rand_mean"], "d_md": r["d_rand_med"]}))
    R = pd.concat(recs, ignore_index=True)
    R["nondeg"] = (R["d_top"] > 1e-12) | (R["d_md"] > 1e-12); R["beat"] = R["d_top"] > R["d_md"]
    R["tersaturasi"] = np.where((R["y0"] <= 1e-12) | (R["y0"] >= 1 - 1e-12), "keluaran terjepit (0 atau 1)", "tidak terjepit")
    R["periode"] = np.where(R["week"] >= np.datetime64(CUT), "sejak 2026-06-08", "sebelum 2026-06-08")
    R["kelompok"] = np.where(R["asset"].str.startswith("p0"), "P0 dan P0-IF", "image resmi")
    pooled = summ(R)
    print("== 1. reproduksi run tercatat ==")
    files = sorted(glob.glob(str(root / e6.OUT_DIR / "e6_results_*.json")))
    if files:
        j = json.load(open(files[-1]))["h6c"]
        same = abs(pooled["rasio"] - j["ratio"]) < 1e-9 and abs(pooled["frac_teratas_menang"] - j["frac"]) < 1e-9 and pooled["degenerat"] == j["n_degenerate"] and pooled["baris"] == j["n_rows"]
        print(f"  tercatat: rasio={j['ratio']:.4f} frac={j['frac']:.4f} degenerat={j['n_degenerate']} baris={j['n_rows']} | ulang: rasio={pooled['rasio']:.4f} frac={pooled['frac_teratas_menang']:.4f} degenerat={pooled['degenerat']} baris={pooled['baris']}")
        print("  REPRODUKSI " + ("COCOK" if same else "TIDAK COCOK (hentikan; sebaran di bawah tidak boleh ditafsirkan)"))
    else:
        print("  tidak ada e6_results_*.json")
    print("== 2. sebaran H6c (deskriptif; keputusan tidak berubah) ==")
    rows_out = []
    for col in ("fold", "periode", "kelompok", "tersaturasi"):
        for name, g in R.groupby(col):
            s = summ(g); rows_out.append({"strata": col, "nilai": str(name), **s})
            print(f"  {col:11} {str(name):30} baris={s['baris']:5} degenerat={s['degenerat']:4} teratas>median acak={s['frac_teratas_menang']:.3f} rasio={s['rasio']:.2f}")
    print("== 3. H6a pada pasangan S+ (seluruh minggu, 25 model) ==")
    on = df[df["asset"] == "p0if-on"].set_index("week"); off = df[df["asset"] == "p0if-off"].set_index("week"); weeks = sorted(set(on.index) & set(off.index))
    ion = np.array([idx[on.loc[w, "event_id"]] for w in weeks]); ioff = np.array([idx[off.loc[w, "event_id"]] for w in weeks])
    Xon, Xoff = X[ion], X[ioff]; okp = ~(np.isnan(Xon).any(1) | np.isnan(Xoff).any(1))
    dx2 = (on.loc[weeks, "exploitability"].to_numpy(float) - off.loc[weeks, "exploitability"].to_numpy(float))[okp]; splus = dx2 > 1e-6
    print(f"  minggu dikecualikan karena NaN: {int((~okp).sum())} dari {len(weeks)}; S+={int(splus.sum())}, S0={int((~splus).sum())}")
    tot = up = clamp_off = clamp_both = 0; dsum = []
    for key, ad in sorted(ads.items()):
        yon, yoff = ad.forward(Xon[okp]), ad.forward(Xoff[okp]); d = (yon - yoff)[splus]
        tot += len(d); up += int((d > 1e-12).sum()); clamp_off += int((yoff[splus] <= 1e-12).sum()); clamp_both += int(((yoff[splus] <= 1e-12) & (yon[splus] <= 1e-12)).sum()); dsum.append(d.mean())
    print(f"  pasangan S+ x model = {tot}; benar-benar naik (> 1e-12) = {up} ({up / max(tot, 1):.3f}); keluaran OFF terjepit di 0 = {clamp_off}; ON dan OFF sama-sama 0 = {clamp_both}")
    print(f"  rerata y_hat(on)-y_hat(off) pada S+ (skala 0-100) = {100 * float(np.mean(dsum)):.5f}")
    print("== 4. kontras ON-OFF pada minggu UJI: model (rata-rata 5 seed) vs label ==")
    if "y_true" in preds.columns:
        p = preds[preds["event_id"].str.startswith(("p0if-on__", "p0if-off__"))].copy(); p["asset"] = p["event_id"].str.rsplit("__", n=1).str[0]; p["week"] = p["event_id"].str.rsplit("__", n=1).str[1]
        pv = p.pivot(index="week", columns="asset", values=["y_hanfis", "y_true"]).dropna()
        dm = pv["y_hanfis"]["p0if-on"] - pv["y_hanfis"]["p0if-off"]; dl = pv["y_true"]["p0if-on"] - pv["y_true"]["p0if-off"]
        print(f"  minggu uji berpasangan = {len(pv)}; rerata kontras model = {dm.mean():.5f}; rerata kontras label = {dl.mean():.5f}")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()); outp = root / e6.OUT_DIR; outp.mkdir(parents=True, exist_ok=True)
    R.drop(columns=["week"]).assign(week=R["week"].astype(str)).to_csv(outp / f"e6_h6c_rows_{stamp}.csv", index=False)
    (outp / f"e6_descriptives_{stamp}.json").write_text(json.dumps({"deskriptif": True, "pooled": pooled, "strata": rows_out, "h6a": {"pasangan": tot, "naik": up, "off_terjepit": clamp_off}}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"STATUS=E6_DESCRIPTIVES_DONE ({outp}/e6_descriptives_{stamp}.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
