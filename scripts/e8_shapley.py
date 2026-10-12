#!/usr/bin/env python3
"""E8 -- atribusi Shapley eksak (interventional) untuk 25 model HANFIS tersimpan: dampak fitur global, sebaran atribusi, irisan, dan pemeriksaan arah. DESKRIPTIF, post hoc.

Penerapan ide 'SHAP impact / SHAP distributions / data slice' pada HANFIS: dengan 7 masukan, nilai Shapley dihitung EKSAK dari 2^7 = 128 koalisi (bukan perkiraan).
  v(S; x) = rerata atas latar belakang b dari f(x_S, b_bukan-S) ;  phi_j(x) = jumlah atas S tanpa j dari bobot(|S|) * (v(S+j) - v(S)) ;  jumlah phi = f(x) - rerata f(latar belakang).
Satuan: poin skor (0-100). Latar belakang: K baris acak dari seluruh baris berlabel selain P0/P0-IF (seed tetap), sama untuk semua model.
Keluaran: results_python/e8/e8_shapley_rows_*.csv, e8_summary_*.json, dan tabel ringkas di layar. Tidak ada kriteria keputusan; tidak mengubah hasil E4/E6.
  python scripts/e8_shapley.py [--background-k 12] [--bg-seed 20261009]"""
import argparse, itertools, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import e6_explain as e6

NAMES_ID = {"cvss": "x1 CVSS", "exploitability": "x2 Exploitability (EPSS x rho)", "patch_risk": "x3 Patch Risk", "mfa_risk": "x4 MFA Risk",
            "kubernetes_exposure": "x5 Kubernetes Exposure", "asset_criticality": "x6 Asset Criticality", "threat_intelligence": "x7 Threat Intelligence (KEV)"}
LABEL_OVERLAP = ("exploitability", "threat_intelligence")   # bahan label yang juga masukan (x2, x7)
CUT = pd.Timestamp("2026-06-08")


def shapley_exact(f, X, B):
    """f: fungsi (M,d)->(M,) ; X: (N,d) ; B: (K,d) latar belakang. Mengembalikan phi (N,d), dan base (rerata f(B)), serta f(X)."""
    N, d = X.shape; K = len(B)
    nmask = 1 << d
    v = np.empty((nmask, N))
    for m in range(nmask):
        keep = np.array([(m >> j) & 1 for j in range(d)], dtype=bool)
        Z = np.where(keep[None, None, :], X[None, :, :], B[:, None, :]).reshape(K * N, d)      # (K,N,d) -> (K*N,d)
        v[m] = f(Z).reshape(K, N).mean(0)
    w = [math.factorial(s) * math.factorial(d - s - 1) / math.factorial(d) for s in range(d)]
    phi = np.zeros((N, d))
    for j in range(d):
        for m in range(nmask):
            if (m >> j) & 1: continue
            s = bin(m).count("1")
            phi[:, j] += w[s] * (v[m | (1 << j)] - v[m])
    return phi, float(v[0].mean()), v[nmask - 1]


def ice_monotone(f, X, j, grid, tol=1e-9, detail=False):
    """Uji monotonisitas DALAM-BARIS: ubah x_j pada grid, semua masukan lain tetap. Mengembalikan (fraksi langkah yang turun > tol, penurunan terbesar, rerata |f(ujung) - f(awal)|)."""
    G, N = len(grid), len(X)
    Z = np.repeat(X[None, :, :], G, axis=0).copy(); Z[:, :, j] = grid[:, None]
    y = f(Z.reshape(G * N, -1)).reshape(G, N); d = np.diff(y, axis=0)
    out = (float((d < -tol).mean()), float(max(0.0, -d.min())), float(np.abs(y[-1] - y[0]).mean()))
    return out + (np.maximum(0.0, -d).max(0),) if detail else out


def support_grid(col, n=11):
    """Grid dalam dukungan data: nilai unik teramati bila <= 6 nilai (masukan diskret), selain itu kuantil 1%..99% (n titik)."""
    c = col[~np.isnan(col)]; u = np.unique(np.round(c, 6))
    return u if len(u) <= 6 else np.quantile(c, np.linspace(0.01, 0.99, n))


def kendall_w(rank_matrix):
    """rank_matrix: (m penilai, n objek) peringkat 1..n. Kendall's W tanpa koreksi ikatan."""
    m, n = rank_matrix.shape; R = rank_matrix.sum(0); S = ((R - R.mean()) ** 2).sum()
    return float(12 * S / (m ** 2 * (n ** 3 - n)))


def share_table(df, cols):
    a = df[cols].abs().mean()
    return (a / a.sum()), a


def main(argv=None, adapters64=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--background-k", type=int, default=12); ap.add_argument("--bg-seed", type=int, default=20261009); ap.add_argument("--ice-grid", type=int, default=11); ap.add_argument("--material-tol", type=float, default=0.05); ap.add_argument("--detail-min", type=float, default=1.0)
    a = ap.parse_args(argv); root = Path(a.root).resolve()
    meta = json.load(open(root / e6.MODELS_DIR / e6.META_FILE)); table = pd.read_csv(root / e6.TABLE); preds = pd.read_csv(root / e6.MODELS_DIR / e6.PRED_FILE)
    df, X = e6.build_inputs(table, meta); order = meta["inputs_order"]; d = len(order)
    ads = adapters64 if adapters64 is not None else e6.load_torch_adapters(root, meta, True)
    idx = {e: i for i, e in enumerate(df["event_id"])}
    wk = pd.to_datetime(df["week_start_utc"], utc=True).dt.tz_localize(None).to_numpy()
    # latar belakang: baris berlabel selain P0/P0-IF, tanpa NaN
    ok = df["y"].notna().to_numpy() & ~df["asset"].str.startswith("p0").to_numpy() & ~np.isnan(X).any(1)
    rng = np.random.default_rng(a.bg_seed); B = X[rng.choice(np.where(ok)[0], size=a.background_k, replace=False)]
    sup_grids = [support_grid(X[ok][:, j]) for j in range(d)]
    (root / "results_python" / "e8").mkdir(parents=True, exist_ok=True)
    recs = []; ice_rows = []; viol_rows = []; t0 = time.time(); worst_eff = 0.0
    for key, ad in sorted(ads.items()):
        sub = preds[preds["fold"] == key[0]]; rows = np.array([idx[e] for e in sub["event_id"]]); Xt = X[rows]; keep = ~np.isnan(Xt).any(1); rows, Xt, sub = rows[keep], Xt[keep], sub[keep]
        f = lambda Z: 100.0 * ad.forward(Z)
        phi, base, fx_bar = shapley_exact(f, Xt, B)
        fx = f(Xt); worst_eff = max(worst_eff, float(np.abs(phi.sum(1) - (fx - base)).max()))
        r = pd.DataFrame(phi, columns=[f"phi_{c}" for c in order]); r.insert(0, "fold", key[0]); r.insert(1, "seed", key[1]); r.insert(2, "event_id", df["event_id"].to_numpy()[rows])
        r["asset"] = df["asset"].to_numpy()[rows]; r["week"] = wk[rows]; r["pred"] = fx; r["base"] = base; r["y_true"] = sub["y_true"].to_numpy() if "y_true" in sub.columns else np.nan
        for j, c in enumerate(order): r[f"x_{c}"] = Xt[:, j]
        recs.append(r)
        for j, c in enumerate(order):
            vr, md, ef = ice_monotone(f, Xt, j, np.linspace(0.0, 1.0, a.ice_grid)); vs, ms_, es, rd = ice_monotone(f, Xt, j, sup_grids[j], detail=True); hit = np.where(rd > a.detail_min)[0]
            if len(hit): viol_rows.append(pd.DataFrame({"fold": key[0], "seed": key[1], "input": c, "event_id": df["event_id"].to_numpy()[rows][hit], "asset": df["asset"].to_numpy()[rows][hit], "week": wk[rows][hit], "x_atual": Xt[hit, j], "max_turun": rd[hit], "pred": fx[hit]}))
            vm, _, _ = ice_monotone(f, Xt, j, sup_grids[j], tol=a.material_tol)
            ice_rows.append({"fold": key[0], "seed": key[1], "input": c, "pelanggaran": vr, "turun_maks": md, "efek_rentang": ef, "pel_dukungan": vs, "turun_dukungan": ms_, "efek_dukungan": es, "pel_material": vm})
    R = pd.concat(recs, ignore_index=True); pc = [f"phi_{c}" for c in order]
    print(f"== E8: Shapley eksak ({len(ads)} model, {len(R)} baris, latar belakang K={a.background_k}, {time.time() - t0:.0f} dtk) ==")
    print(f"  pemeriksaan efisiensi (jumlah phi = f(x) - basis): selisih maks {worst_eff:.2e}  ->  " + ("OK" if worst_eff < 1e-6 else "PERIKSA: batas toleransi float"))
    sh, ab = share_table(R, pc); sh, ab = sh.to_numpy(), ab.to_numpy()
    print("== 1. dampak global (rerata |phi|, poin skor; porsi) ==")
    for c, s, v in sorted(zip(order, sh, ab), key=lambda t: -t[1]): print(f"  {NAMES_ID.get(c, c):42} {v:7.3f}  {100 * s:5.1f}%")
    ov = sum(sh[order.index(c)] for c in LABEL_OVERLAP if c in order)
    print(f"  porsi bahan label yang juga masukan (x2 + x7): {100 * ov:.1f}%   [petunjuk beban sirkularitas label-masukan]")
    # stabilitas peringkat antar model
    per_model = R.groupby(["fold", "seed"])[pc].apply(lambda g: g.abs().mean()); ranks = per_model.rank(axis=1, ascending=False).to_numpy()
    W = kendall_w(ranks); top = pd.Series(per_model.idxmax(axis=1)).value_counts()
    print(f"== 2. stabilitas antar {len(per_model)} model: Kendall W = {W:.3f}; fitur teratas per model: " + ", ".join(f"{k.replace('phi_', '')}={v}" for k, v in top.items()))
    # arah: korelasi Spearman phi_j dengan x_j per model
    dirs = {}
    import warnings
    for c in order:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            vals = [g[f"phi_{c}"].rank().corr(g[f"x_{c}"].rank()) for _, g in R.groupby(["fold", "seed"])]; dirs[c] = float(np.nanmean(vals)) if np.isfinite(vals).any() else float("nan")
    ICE = pd.DataFrame(ice_rows); icg = ICE.groupby("input").agg(pel=("pelanggaran", "mean"), pel_maks=("pelanggaran", "max"), turun=("turun_maks", "max"), efek=("efek_rentang", "mean"),
                                                                   pel_d=("pel_dukungan", "mean"), pel_d_maks=("pel_dukungan", "max"), turun_d=("turun_dukungan", "max"), efek_d=("efek_dukungan", "mean"), pel_m=("pel_material", "mean")).reindex(order)
    print(f"== 3. monotonisitas dalam-baris (ICE; x_j pada grid {a.ice_grid} titik 0..1, masukan lain tetap; pelanggaran = langkah turun > 1e-9) ==")
    print(f"  (a) rentang penuh 0..1 | (b) DALAM-DUKUNGAN data (nilai teramati bila diskret, selain itu kuantil 1%..99%) | (c) seperti (b) tetapi hanya penurunan > {a.material_tol} poin")
    for c in order: print(f"  {NAMES_ID.get(c, c):42} (a) {100 * icg.loc[c, 'pel']:6.2f}% | (b) {100 * icg.loc[c, 'pel_d']:6.2f}% (terburuk {100 * icg.loc[c, 'pel_d_maks']:6.2f}%) | (c) {100 * icg.loc[c, 'pel_m']:6.2f}% | turun terbesar (b) {icg.loc[c, 'turun_d']:.3f} poin | efek rentang (b) {icg.loc[c, 'efek_d']:.3f} poin")
    # --- ENSEMBEL: rata-rata seed dalam tiap fold (prediktor yang dilaporkan di E4)
    ens = {c: {"b": [], "c": [], "drop": [], "eff": []} for c in order}
    for fold in sorted({k[0] for k in ads}):
        members = [ad for (fo, se), ad in sorted(ads.items()) if fo == fold]
        sub = preds[preds["fold"] == fold]; rws = np.array([idx[e] for e in sub["event_id"]]); Xf = X[rws]; Xf = Xf[~np.isnan(Xf).any(1)]
        fe = lambda Z, m=members: 100.0 * np.mean([ad.forward(Z) for ad in m], axis=0)
        for j, c in enumerate(order):
            vs, ms_, es = ice_monotone(fe, Xf, j, sup_grids[j]); vm, _, _ = ice_monotone(fe, Xf, j, sup_grids[j], tol=a.material_tol)
            ens[c]["b"].append(vs); ens[c]["c"].append(vm); ens[c]["drop"].append(ms_); ens[c]["eff"].append(es)
    print(f"== 3c. ENSEMBEL (rata-rata 5 seed per fold = prediktor yang dilaporkan), dalam-dukungan: (b) semua penurunan, (c) hanya > {a.material_tol} poin ==")
    for c in order:
        e = ens[c]; print(f"  {NAMES_ID.get(c, c):42} (b) {100 * np.mean(e['b']):6.2f}% | (c) {100 * np.mean(e['c']):6.2f}% | fold terburuk (c) {100 * np.max(e['c']):6.2f}% | turun terbesar {np.max(e['drop']):.3f} poin | efek rentang {np.mean(e['eff']):.3f} poin")
    ens_summary = {c: {"b": float(np.mean(ens[c]["b"])), "c": float(np.mean(ens[c]["c"])), "c_terburuk": float(np.max(ens[c]["c"])), "turun_maks": float(np.max(ens[c]["drop"])), "efek": float(np.mean(ens[c]["eff"]))} for c in order}
    if viol_rows:
        V = pd.concat(viol_rows, ignore_index=True); V["week"] = V["week"].astype(str)
        print(f"== 3a. penurunan besar dalam-dukungan (> {a.detail_min} poin): pasangan model-baris per masukan, baris unik, dan konsentrasi per aset ==")
        for c in order:
            g = V[V["input"] == c]
            if g.empty: print(f"  {NAMES_ID.get(c, c):42} tidak ada"); continue
            top = g.groupby("asset").size().sort_values(ascending=False)
            print(f"  {NAMES_ID.get(c, c):42} {len(g):5d} pasangan, {g['event_id'].nunique():4d} baris unik, {g['asset'].nunique():3d} aset; 3 aset teratas: " + ", ".join(f"{k}({v})" for k, v in top.head(3).items()) + f"; turun terbesar {g['max_turun'].max():.2f}")
        print("  12 kasus terbesar:"); print(V.sort_values("max_turun", ascending=False).head(12)[["input", "event_id", "x_atual", "max_turun", "pred", "fold", "seed"]].round(3).to_string(index=False))
        V.to_csv(root / "results_python" / "e8" / f"e8_ice_violations_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.csv", index=False)
    print("== 3b. asosiasi lintas baris Spearman(phi_j, x_j) -- BUKAN uji monotonisitas: tercampur perbedaan antar-aset dan korelasi antar-masukan ==")
    for c in order: print(f"  {NAMES_ID.get(c, c):42} {dirs[c]:+.3f}")
    # sebaran
    qs = R[pc].quantile([0.05, 0.25, 0.5, 0.75, 0.95]).T; qs.index = order
    print("== 4. sebaran phi (kuantil 5/25/50/75/95) ==\n" + qs.round(3).to_string())
    # irisan
    R["periode"] = np.where(R["week"] >= np.datetime64(CUT), "sejak 2026-06-08", "sebelum 2026-06-08"); R["kelompok"] = np.where(R["asset"].str.startswith("p0"), "P0 dan P0-IF", "image resmi")
    thr = R["y_true"].quantile(0.8) if R["y_true"].notna().any() else np.nan
    R["label"] = np.where(R["y_true"] >= thr, "label 20% teratas", "lainnya")
    print("== 5. irisan: porsi dampak (%) per masukan ==")
    sl = {}
    for col in ("periode", "kelompok", "label"):
        for name, g in R.groupby(col):
            s, _ = share_table(g, pc); s = s.to_numpy(); sl[f"{col}={name}"] = {"baris": int(len(g)), **{c: float(100 * v) for c, v in zip(order, s)}}
            print(f"  {col}={name:22} n={len(g):5d}  " + "  ".join(f"{c[:5]}={100 * v:4.1f}" for c, v in zip(order, s)))
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()); od = root / "results_python" / "e8"; od.mkdir(parents=True, exist_ok=True)
    R.drop(columns=["week"]).assign(week=R["week"].astype(str)).to_csv(od / f"e8_shapley_rows_{stamp}.csv", index=False)
    (od / f"e8_summary_{stamp}.json").write_text(json.dumps({"deskriptif": True, "model": len(ads), "baris": int(len(R)), "latar_belakang_k": a.background_k, "bg_seed": a.bg_seed, "efisiensi_selisih_maks": worst_eff,
        "porsi_global": dict(zip(order, map(float, sh))), "rerata_abs_phi": dict(zip(order, map(float, ab))), "porsi_bahan_label": float(ov), "kendall_w": W, "arah_spearman_lintas_baris": dirs, "ice_ensembel_dalam_dukungan": ens_summary, "ice_monotonisitas": {c: {k: float(v) for k, v in icg.loc[c].items()} for c in order}, "irisan": sl}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"STATUS=E8_SHAPLEY_DONE ({od}/e8_summary_{stamp}.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
