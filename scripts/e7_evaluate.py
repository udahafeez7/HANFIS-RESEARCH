#!/usr/bin/env python3
"""E7 -- evaluasi prospektif (draf praregistrasi: protocols/E7_preregistration_DRAFT.md). Hanya numpy dan pandas.
Masukan: CSV prediksi forward dengan kolom event_id, y_true, y_hanfis, y_lag4 (pilihan: y_ridge7, week, dx2_4w, dkev_4w, epss_model_version).
  --rehearsal : jalankan kode yang sama pada berkas MANA SAJA (mis. prediksi out-of-fold E4) untuk menguji jalur kode. HASILNYA BUKAN HASIL E7.
  --run       : analisis resmi; MENOLAK berjalan kecuali scripts/verify_prereg_tag.py LOLOS untuk --tag dan --files (isi pohon tag = berkas kerja).
Hibrida: y_hat = lambda * y_hanfis + (1 - lambda) * y_lag4, lambda dari protocols/E7_lambda_<tanggal>.json (tidak disetel).
Keputusan: P7a (HANFIS tidak lebih baik di minggu stabil), P7b (hibrida mengalahkan persistence), P7c (presisi@20%, non-inferioritas), Holm pada {P7a, P7b}."""
import argparse, json, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

SESOI, NONINF, TOP, MIN_WEEKS = 0.05, -0.05, 0.20, 6


def ss(sse_m, sse_p):
    return 1.0 - sse_m / sse_p


def group_sums(df, pred_cols, groups):
    gi = {g: i for i, g in enumerate(groups)}
    idx = df["grup"].map(gi).to_numpy()
    out = {}
    for c in pred_cols:
        a = np.zeros(len(groups)); np.add.at(a, idx, (df[c].to_numpy() - df["y_true"].to_numpy()) ** 2); out[c] = a
    return out


def boot_ss(df, methods, groups, rng, B, base="y_lag4"):
    """SS terhadap persistence untuk tiap metode: titik, CI95, dan sampel bootstrap (bootstrap berkelompok per image)."""
    gs = group_sums(df, [base] + methods, groups)
    G = len(groups); counts = rng.multinomial(G, np.full(G, 1.0 / G), size=B)
    res = {}
    for m in methods:
        pt = ss(gs[m].sum(), gs[base].sum()); bs = 1.0 - (counts @ gs[m]) / (counts @ gs[base])
        res[m] = {"ss": float(pt), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "boot": bs}
    return res


def prec_at(y, p, frac=TOP):
    k = max(1, int(np.ceil(frac * len(y))))
    ty = set(np.argsort(-y, kind="stable")[:k]); tp = set(np.argsort(-p, kind="stable")[:k])
    return len(ty & tp) / k


def weekly_precision(df, cols, rng=None, counts=None, groups_idx=None):
    out = {c: [] for c in cols}
    for _, g in df.groupby("week"):
        rows = np.arange(len(g)); gi = g["gidx"].to_numpy()
        if counts is not None: rows = np.repeat(rows, counts[gi])
        if len(rows) < 5: continue
        y = g["y_true"].to_numpy()[rows]
        for c in cols: out[c].append(prec_at(y, g[c].to_numpy()[rows]))
    return {c: float(np.mean(v)) if v else float("nan") for c, v in out.items()}


def boot_precision(df, cols, groups, rng, B):
    gi = {g: i for i, g in enumerate(groups)}; df = df.copy(); df["gidx"] = df["grup"].map(gi)
    pt = weekly_precision(df, cols)
    G = len(groups); diffs = []
    for _ in range(B):
        counts = rng.multinomial(G, np.full(G, 1.0 / G)); b = weekly_precision(df, cols, counts=counts)
        diffs.append(b["y_hibrida"] - b["y_lag4"])
    return pt, [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]


def spearman_weekly(df, cols):
    out = {}
    for c in cols:
        r = [g["y_true"].rank().corr(g[c].rank()) for _, g in df.groupby("week") if len(g) >= 5]
        out[c] = float(np.nanmean(r)) if r else float("nan")
    return out


def verify(tag, files):
    here = Path(__file__).with_name("verify_prereg_tag.py")
    return subprocess.run([sys.executable, str(here), tag, *files], capture_output=True, text=True)


def main(argv=None, verifier=None):
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--rehearsal", action="store_true"); g.add_argument("--run", action="store_true")
    ap.add_argument("--pred", required=True); ap.add_argument("--lambda-json", required=True); ap.add_argument("--tag"); ap.add_argument("--files", nargs="*", default=[])
    ap.add_argument("--col-lag4", default="y_lag4"); ap.add_argument("--col-ridge", default="y_ridge7"); ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261102); ap.add_argument("--out-dir", default="results_python/e7"); a = ap.parse_args(argv)
    if a.run:
        if not a.tag or not a.files: sys.exit("ABORT: --run memerlukan --tag dan --files (protokol, skrip, lambda, hash model)")
        r = verifier() if verifier else verify(a.tag, a.files)
        ok = r if isinstance(r, bool) else r.returncode == 0
        if not ok:
            print("STATUS=HOLD_E7_PREREG_NOT_VERIFIED"); print(getattr(r, "stdout", "")); return 2
    lam = json.load(open(a.lambda_json))["lambda"]
    df = pd.read_csv(a.pred).rename(columns={a.col_lag4: "y_lag4", a.col_ridge: "y_ridge7"})
    need = {"event_id", "y_true", "y_hanfis", "y_lag4"}
    if not need <= set(df.columns): sys.exit(f"ABORT: kolom kurang: {sorted(need - set(df.columns))}")
    if "week" not in df.columns: df["week"] = df["event_id"].str.rsplit("__", n=1).str[1]
    df = df.dropna(subset=list(need - {"event_id"})).copy()
    df["grup"] = df["event_id"].str.rsplit("__", n=1).str[0].str.replace(r"-(on|off)$", "", regex=True)
    df["y_hibrida"] = lam * df["y_hanfis"] + (1 - lam) * df["y_lag4"]
    weeks = sorted(df["week"].unique()); groups = sorted(df["grup"].unique())
    if len(weeks) < MIN_WEEKS:
        print(f"STATUS=HOLD_E7_TOO_FEW_WEEKS ({len(weeks)} < {MIN_WEEKS}); E7 ditunda, tidak dilonggarkan"); return 3
    rng = np.random.default_rng(a.seed); out = {"mode": "REHEARSAL (bukan hasil E7)" if a.rehearsal else "RUN", "lambda": lam, "minggu": len(weeks), "baris": int(len(df)), "kelompok": len(groups)}
    stable = df
    if "epss_model_version" in df.columns and df["epss_model_version"].nunique() > 1:
        first = df.sort_values("week")["epss_model_version"].iloc[0]; stable = df[df["epss_model_version"] == first]
        out["catatan_versi_epss"] = f"{df['epss_model_version'].nunique()} versi; P7a hanya pada versi {first} ({stable['week'].nunique()} minggu)"
    methods = ["y_hanfis", "y_hibrida"] + (["y_ridge7"] if "y_ridge7" in df.columns else [])
    bs_all = boot_ss(df, methods, groups, rng, a.boot); bs_st = boot_ss(stable, ["y_hanfis"], sorted(stable["grup"].unique()), rng, a.boot)
    sa, sb = bs_st["y_hanfis"], bs_all["y_hibrida"]
    p_a = (1 + int((sa["boot"] >= SESOI).sum())) / (a.boot + 1); p_b = (1 + int((sb["boot"] <= 0).sum())) / (a.boot + 1)
    order = sorted([("P7a", p_a), ("P7b", p_b)], key=lambda t: t[1]); holm = {}
    for i, (k, p) in enumerate(order):
        holm[k] = {"p_satu_sisi": p, "ambang_holm": 0.025 / (2 - i), "lolos": bool(p <= 0.025 / (2 - i))}
        if not holm[k]["lolos"]:
            for k2, _ in order[i + 1:]: holm[k2] = {"p_satu_sisi": dict(order)[k2], "ambang_holm": 0.025 / (2 - i - 1), "lolos": False}
            break
    v_a = "DIDUKUNG" if (sa["ci95"][1] < SESOI and holm["P7a"]["lolos"]) else ("DIBANTAH" if (sa["ss"] >= SESOI and sa["ci95"][0] > 0) else "TIDAK TERBUKTI")
    v_b = "TERKONFIRMASI" if (sb["ss"] >= SESOI and sb["ci95"][0] > 0 and holm["P7b"]["lolos"]) else ("LEBIH BURUK" if sb["ci95"][1] < 0 else "TIDAK TERKONFIRMASI")
    pc_cols = ["y_hanfis", "y_lag4", "y_hibrida"] + (["y_ridge7"] if "y_ridge7" in df.columns else [])
    pt, ci = boot_precision(df, pc_cols, groups, rng, min(a.boot, 1000)); delta = pt["y_hibrida"] - pt["y_lag4"]
    v_c = "NON-INFERIOR" if ci[0] > NONINF else "TIDAK TERBUKTI NON-INFERIOR"
    out.update({"P7a": {"ss_hanfis_stabil": sa["ss"], "ci95": sa["ci95"], "keputusan": v_a, "holm": holm["P7a"]},
                "P7b": {"ss_hibrida": sb["ss"], "ci95": sb["ci95"], "keputusan": v_b, "holm": holm["P7b"]},
                "P7c": {"presisi_pada_20persen": pt, "selisih_hibrida_minus_persistence": delta, "ci95_selisih": ci, "keputusan": v_c, "spearman_mingguan": spearman_weekly(df, pc_cols)},
                "ss_semua_metode": {m: {"ss": bs_all[m]["ss"], "ci95": bs_all[m]["ci95"]} for m in methods}})
    strata = {}
    if {"dx2_4w", "dkev_4w"} <= set(df.columns):
        ch = (df["dx2_4w"].abs() > 1e-9) | (df["dkev_4w"].abs() > 0)
        for name, sub in (("ada_perubahan_masukan", df[ch]), ("tanpa_perubahan_masukan", df[~ch])):
            if len(sub) >= 20 and sub["grup"].nunique() >= 5:
                b = boot_ss(sub, ["y_hanfis", "y_hibrida"], sorted(sub["grup"].unique()), rng, a.boot); strata[name] = {"baris": int(len(sub)), **{m: {"ss": b[m]["ss"], "ci95": b[m]["ci95"]} for m in b}}
            else: strata[name] = {"baris": int(len(sub)), "catatan": "terlalu sedikit untuk CI"}
    out["strata_deskriptif"] = strata
    sens = {}
    if "lambda_per_fold" in json.load(open(a.lambda_json)):
        for f, l in json.load(open(a.lambda_json))["lambda_per_fold"].items():
            h = l * df["y_hanfis"] + (1 - l) * df["y_lag4"]; sens[f"ss_hibrida_lambda_fold_{f}"] = ss(((h - df["y_true"]) ** 2).sum(), ((df["y_lag4"] - df["y_true"]) ** 2).sum())
    lg = lambda s: np.log1p(np.clip(s, 0, None) / 100.0)
    sens["ss_hanfis_log1p"] = ss(((lg(df["y_hanfis"]) - lg(df["y_true"])) ** 2).sum(), ((lg(df["y_lag4"]) - lg(df["y_true"])) ** 2).sum())
    sens["ss_hibrida_log1p"] = ss(((lg(df["y_hibrida"]) - lg(df["y_true"])) ** 2).sum(), ((lg(df["y_lag4"]) - lg(df["y_true"])) ** 2).sum())
    nw = df[~df["grup"].str.contains("wordpress", case=False)]
    if len(nw) < len(df): sens["ss_hibrida_tanpa_wordpress"] = ss(((nw["y_hibrida"] - nw["y_true"]) ** 2).sum(), ((nw["y_lag4"] - nw["y_true"]) ** 2).sum())
    out["sensitivitas_deskriptif"] = sens
    print(f"== {out['mode']} | lambda={lam:.4f} | minggu={len(weeks)} baris={len(df)} kelompok={len(groups)} ==")
    print(f"P7a SS_HANFIS(stabil)={sa['ss']:+.3f} CI95 [{sa['ci95'][0]:+.3f}, {sa['ci95'][1]:+.3f}]  -> {v_a} (Holm p={p_a:.4f}, lolos={holm['P7a']['lolos']})")
    print(f"P7b SS_hibrida      ={sb['ss']:+.3f} CI95 [{sb['ci95'][0]:+.3f}, {sb['ci95'][1]:+.3f}]  -> {v_b} (Holm p={p_b:.4f}, lolos={holm['P7b']['lolos']})")
    print(f"P7c presisi@20%: " + ", ".join(f"{k}={v:.3f}" for k, v in pt.items()) + f" | selisih hibrida-persistence={delta:+.3f} CI95 [{ci[0]:+.3f}, {ci[1]:+.3f}] -> {v_c}")
    for k, v in strata.items(): print(f"strata {k}: {v}")
    od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=True); fp = od / f"e7_{'rehearsal' if a.rehearsal else 'results'}_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    fp.write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
    print(f"STATUS={'E7_REHEARSAL_DONE (bukan hasil E7)' if a.rehearsal else 'E7_RUN_DONE'} ({fp})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
