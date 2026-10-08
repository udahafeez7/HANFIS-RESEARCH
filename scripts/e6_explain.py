#!/usr/bin/env python3
"""E6 -- kesetiaan penjelasan HANFIS (draf praregistrasi: protocols/E6_preregistration_DRAFT.md).

Seluruh analisis ditulis dalam numpy; hanya kelas TorchAdapter yang menyentuh torch.
  --smoke : memuat model E4-bis, memeriksa replikasi prediksi (TANPA baris P0-IF, TANPA label) dan sifat fungsi pada baris non-P0-IF;
            jalur H6c hanya dieksekusi pada masukan SINTETIS (nilainya tidak dilaporkan). Aman dijalankan sebelum praregistrasi dibekukan.
  --run   : analisis penuh. MENOLAK berjalan bila belum ada tag git 'e6-prereg-*' (praregistrasi dibekukan lebih dulu).
Jalankan dari akar repo:  python scripts/e6_explain.py --smoke      |      python scripts/e6_explain.py --run
"""
import argparse, copy, json, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

TABLE = "data/processed/asset_weeks_v2_120assets_e4bis.csv"
MODELS_DIR = "results_python/e4bis_120_models"
PRED_FILE = "predictions_20261005T083407Z.csv"
META_FILE = "meta_20261005T083407Z.json"
OUT_DIR = "results_python/e6"
EPS = 1e-9


# ----------------------------------------------------------------------------------------------------------------- adaptor torch
class TorchAdapter:
    """Satu-satunya bagian yang menyentuh torch. Antarmuka (dari kode HANFIS): model.vulnerability/environment/integration (SugenoPanel)
    dengan .firing(x) -> (N,R), .effective_consequents() -> (R,1+n_in), pemanggilan panel(x) -> (N,); model.intermediates(x7, clamp=True);
    model.integration_input(x7, clamp=True); model.rule_trace(x7); model(x7)."""
    PANELS = {"vulnerability": "vulnerability", "environment": "environment", "integration": "integration"}

    def __init__(self, model, double):
        import torch
        self.t = torch
        self.dt = torch.float64 if double else torch.float32
        self.m = model.double() if double else model.float()
        self.m.eval()

    def _x(self, X):
        return self.t.as_tensor(np.asarray(X), dtype=self.dt)

    def _np(self, T):
        return T.detach().cpu().numpy().astype(np.float64)

    def forward(self, X7):
        with self.t.no_grad():
            return self._np(self.m(self._x(X7)))

    def trace(self, X7):
        with self.t.no_grad():
            return {k: self._np(v) for k, v in self.m.rule_trace(self._x(X7)).items()}

    def inter(self, X7):
        with self.t.no_grad():
            v, e = self.m.intermediates(self._x(X7), clamp=True)
            return self._np(v), self._np(e)

    def firing(self, name, X):
        with self.t.no_grad():
            return self._np(getattr(self.m, name).firing(self._x(X)))

    def beta(self, name):
        with self.t.no_grad():
            return self._np(getattr(self.m, name).effective_consequents())

    def panel_out(self, name, X):
        with self.t.no_grad():
            return self._np(getattr(self.m, name)(self._x(X)))

    def y_from(self, v, e, x7):
        with self.t.no_grad():
            xi = self.t.stack([self._x(v), self._x(e), self._x(x7)], dim=1)
            return self._np(self.t.clamp(self.m.integration(xi), 0.0, 1.0))


def load_torch_adapters(root, meta, double):
    import torch
    sys.path.insert(0, str(root / "python_hanfis"))
    from hanfis_end2end import HANFIS  # noqa: E402
    out = {}
    for ent in meta["saved_models"]:
        path = root / MODELS_DIR / "models" / ent["file"]
        model = HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True)
        try:
            model.load_state_dict(torch.load(path, map_location="cpu"))
        except Exception as ex:
            sys.exit(f"ABORT: state_dict {path.name} tidak cocok dengan HANFIS(m_raw=2, m_intermediate=3, gauss, monotone=True): {str(ex)[:300]}")
        try:
            out[(ent["fold"], ent["seed"])] = TorchAdapter(model, double)
        except Exception as ex:
            if double:
                print(f"PERINGATAN: model tidak dapat diubah ke float64 ({str(ex)[:120]}); memakai float32", file=sys.stderr)
                out[(ent["fold"], ent["seed"])] = TorchAdapter(copy.deepcopy(model), False)
            else:
                raise
    return out


# ----------------------------------------------------------------------------------------------------------------- inti numpy
def parts(X):
    return X[:, 0:3], X[:, 3:6], X[:, 6]


def augment(X):
    return np.concatenate([np.ones((len(X), 1)), X], axis=1)


def contributions(ad, name, X):
    return ad.firing(name, X) * (augment(X) @ ad.beta(name).T)


def stack_i(v, e, x7):
    return np.stack([v, e, x7], axis=1)


def identity_checks(ad, X7):
    """Kontribusi aturan (firing x konsekuen linear) harus menjumlah ke keluaran panel; syarat agar atribusi H6c bermakna."""
    xv, xe, x7 = parts(X7)
    v, e = ad.inter(X7)
    res = {}
    for name, X in (("vulnerability", xv), ("environment", xe), ("integration", stack_i(v, e, x7))):
        res[name] = float(np.abs(contributions(ad, name, X).sum(1) - ad.panel_out(name, X)).max())
    return res


def h6_0(ad, X7):
    """Jejak (rule_trace) harus sama dengan jalur inferensi (intermediate dijepit [0,1], firing integrasi pada intermediate itu)."""
    tr = ad.trace(X7)
    xv, xe, x7 = parts(X7)
    v, e = ad.inter(X7)
    f_int = ad.firing("integration", stack_i(v, e, x7))
    return {"v": float(np.abs(tr["v"] - v).max()), "e": float(np.abs(tr["e"] - e).max()), "integration": float(np.abs(tr["integration"] - f_int).max())}


def pair_checks(ad, Xon, Xoff, splus):
    """H6-neg (S0), H6a, H6b (S+). splus: bool (N,), True bila x2 ON > x2 OFF; S0 = ~splus."""
    d = ad.forward(Xon) - ad.forward(Xoff)
    ton, toff = ad.trace(Xon), ad.trace(Xoff)
    s0 = ~splus
    out = {"n_splus": int(splus.sum()), "n_s0": int(s0.sum())}
    if s0.any():
        out["neg_dy"] = float(np.abs(d[s0]).max())
        out["neg_trace"] = float(max(np.abs(ton[k][s0] - toff[k][s0]).max() for k in ("vulnerability", "environment", "integration", "v", "e")))
    if splus.any():
        out["a_min_dy"] = float(d[splus].min())
        out["b_env_diff"] = float(np.abs(ton["environment"][splus] - toff["environment"][splus]).max())
        out["b_vul_diff"] = float(np.abs(ton["vulnerability"][splus] - toff["vulnerability"][splus]).max())
    return out


def h6c(ad, X7, k, ndraw, rng, h=1e-4):
    """Uji penghapusan: atribusi aturan panel V dan E ke keluaran akhir = kontribusi aturan x turunan y/v (atau y/e); masking = membuang kontribusi aturan
    dari v atau e. Bandingkan |delta y| bila k aturan teratas dihapus dengan k aturan acak."""
    xv, xe, x7 = parts(X7)
    N = len(X7)
    v_raw, e_raw = ad.panel_out("vulnerability", xv), ad.panel_out("environment", xe)
    cv, ce = contributions(ad, "vulnerability", xv), contributions(ad, "environment", xe)
    cl = lambda a: np.clip(a, 0.0, 1.0)
    y0 = ad.y_from(cl(v_raw), cl(e_raw), x7)
    gv = (ad.y_from(cl(v_raw + h), cl(e_raw), x7) - ad.y_from(cl(v_raw - h), cl(e_raw), x7)) / (2 * h)
    ge = (ad.y_from(cl(v_raw), cl(e_raw + h), x7) - ad.y_from(cl(v_raw), cl(e_raw - h), x7)) / (2 * h)
    C = np.concatenate([cv, ce], axis=1)                       # (N,16)
    A = np.concatenate([cv * gv[:, None], ce * ge[:, None]], axis=1)
    R, rV = C.shape[1], cv.shape[1]

    def delta(mask):                                           # mask (N,R) bool -> |dy|
        dv = (C[:, :rV] * mask[:, :rV]).sum(1)
        de = (C[:, rV:] * mask[:, rV:]).sum(1)
        return np.abs(ad.y_from(cl(v_raw - dv), cl(e_raw - de), x7) - y0)

    top = np.argsort(-np.abs(A), axis=1)[:, :k]
    mask_top = np.zeros((N, R), bool)
    np.put_along_axis(mask_top, top, True, axis=1)
    d_top = delta(mask_top)
    d_rand = np.empty((ndraw, N))
    for i in range(ndraw):
        pick = np.argsort(rng.random((N, R)), axis=1)[:, :k]
        m = np.zeros((N, R), bool)
        np.put_along_axis(m, pick, True, axis=1)
        d_rand[i] = delta(m)
    return {"d_top": d_top, "d_rand_mean": d_rand.mean(0), "d_rand_med": np.median(d_rand, axis=0)}


def summarise_h6c(parts_, ratio_thr, frac_thr):
    d_top = np.concatenate([p["d_top"] for p in parts_]); d_rm = np.concatenate([p["d_rand_mean"] for p in parts_]); d_md = np.concatenate([p["d_rand_med"] for p in parts_])
    nd = (d_top > 1e-12) | (d_md > 1e-12)
    ratio = float(d_top.sum() / max(d_rm.sum(), 1e-300))
    frac = float((d_top[nd] > d_md[nd]).mean()) if nd.any() else float("nan")
    return {"ratio": ratio, "frac": frac, "n_rows": int(len(d_top)), "n_degenerate": int((~nd).sum()),
            "pass": bool(ratio >= ratio_thr and frac >= frac_thr)}


# ----------------------------------------------------------------------------------------------------------------- data
def build_inputs(table, meta):
    order = meta["inputs_order"]
    ss = meta["normalisation_shift_scale"]
    df = table.copy()
    df["asset"] = df["event_id"].str.rsplit("__", n=1).str[0]
    df["week"] = df["event_id"].str.rsplit("__", n=1).str[1]
    X = np.stack([(df[c].to_numpy(float) - ss[c][0]) / ss[c][1] for c in order], axis=1)
    return df, X


def replicate(adapters, df, X, preds, exclude_p0if=True):
    """Replikasi prediksi E4 dari model tersimpan (float32): pembuktian bahwa masukan, normalisasi, dan pemuatan sama dengan yang dipakai E4."""
    res = {}
    idx = {e: i for i, e in enumerate(df["event_id"])}
    for fold in sorted(preds["fold"].unique()):
        sub = preds[preds["fold"] == fold]
        if exclude_p0if:
            sub = sub[~sub["event_id"].str.contains("p0if", case=False)]
        rows = [idx[e] for e in sub["event_id"] if e in idx]
        if len(rows) != len(sub):
            sys.exit(f"ABORT: {len(sub) - len(rows)} event_id pada prediksi tidak ada di tabel (fold {fold})")
        Xf = X[rows]
        ok = ~np.isnan(Xf).any(1)
        ys = np.stack([a.forward(Xf[ok]) for (f, s), a in sorted(adapters.items()) if f == fold])
        target = sub["y_hanfis"].to_numpy(float)[: len(rows)][ok]
        best = None
        for agg, y in (("mean", ys.mean(0)), ("median", np.median(ys, 0)), ("seed0", ys[0])):
            for sc in (100.0, 1.0):
                d = float(np.abs(y * sc - target).max())
                if best is None or d < best[2]:
                    best = (agg, sc, d)
        res[int(fold)] = {"agregasi": best[0], "skala": best[1], "maks_selisih": best[2], "n": int(ok.sum()), "n_nan": int((~ok).sum())}
    return res


def analyse(adapters, df, X, preds, meta, args, rng):
    """Analisis penuh E6 pada model (float64)."""
    out = {"h6_0": {}, "ident": {}, "pairs": {}, "h6c_parts": []}
    idx = {e: i for i, e in enumerate(df["event_id"])}
    # --- pasangan P0-IF: seluruh minggu, seluruh model
    on = df[df["asset"] == "p0if-on"].set_index("week")
    off = df[df["asset"] == "p0if-off"].set_index("week")
    weeks = sorted(set(on.index) & set(off.index))
    other = [c for c in meta["inputs_order"] if c != "exploitability"]
    pre = {"minggu_bersama": len(weeks), "kolom_lain_berbeda": {c: int((on.loc[weeks, c] - off.loc[weeks, c]).abs().gt(1e-9).sum()) for c in other}}
    out["tahap0"] = pre
    ion = np.array([idx[on.loc[w, "event_id"]] for w in weeks]); ioff = np.array([idx[off.loc[w, "event_id"]] for w in weeks])
    Xon, Xoff = X[ion], X[ioff]
    okp = ~(np.isnan(Xon).any(1) | np.isnan(Xoff).any(1))
    dx2 = (on.loc[weeks, "exploitability"].to_numpy(float) - off.loc[weeks, "exploitability"].to_numpy(float))[okp]
    splus = dx2 > 1e-6
    pre["s_plus"], pre["s0"], pre["on_lebih_kecil"] = int(splus.sum()), int((np.abs(dx2) <= 1e-6).sum()), int((dx2 < -1e-6).sum())
    for key, ad in sorted(adapters.items()):
        out["pairs"][f"{key[0]}_{key[1]}"] = pair_checks(ad, Xon[okp], Xoff[okp], splus)
    # --- H6-0 dan identitas: semua baris uji + pasangan
    for key, ad in sorted(adapters.items()):
        sub = preds[preds["fold"] == key[0]]
        rows = [idx[e] for e in sub["event_id"] if e in idx]
        Xt = X[rows]; Xt = Xt[~np.isnan(Xt).any(1)]
        out["h6_0"][f"{key[0]}_{key[1]}"] = h6_0(ad, Xt)
        out["ident"][f"{key[0]}_{key[1]}"] = identity_checks(ad, Xt)
        out["h6c_parts"].append(h6c(ad, Xt, args.k, args.ndraw, rng))
    return out


def decide(out, args):
    tol = EPS
    p = out["pairs"]
    h0 = max(max(v.values()) for v in out["h6_0"].values())
    neg = [v["neg_dy"] for v in p.values() if "neg_dy" in v] + [v["neg_trace"] for v in p.values() if "neg_trace" in v]
    a_min = min(v["a_min_dy"] for v in p.values() if "a_min_dy" in v) if any("a_min_dy" in v for v in p.values()) else float("nan")
    b_env = max(v["b_env_diff"] for v in p.values() if "b_env_diff" in v) if any("b_env_diff" in v for v in p.values()) else float("nan")
    b_vul = max(v["b_vul_diff"] for v in p.values() if "b_vul_diff" in v) if any("b_vul_diff" in v for v in p.values()) else float("nan")
    c = summarise_h6c(out["h6c_parts"], args.ratio, args.frac)
    ident = max(max(v.values()) for v in out["ident"].values())
    res = {
        "H6-0": ("PASS" if h0 <= tol else "FAIL", f"maks selisih jejak vs inferensi = {h0:.2e}"),
        "H6-neg": ("TIDAK DAPAT DIEVALUASI" if not neg else ("PASS" if max(neg) <= tol else "FAIL"), "tidak ada pasangan S0" if not neg else f"maks selisih = {max(neg):.2e}"),
        "H6a": ("TIDAK DAPAT DIEVALUASI" if a_min != a_min else ("PASS" if a_min >= -tol else "FAIL"), f"min y(on)-y(off) = {a_min:.3e}"),
        "H6b": ("TIDAK DAPAT DIEVALUASI" if b_env != b_env else ("PASS" if (b_env <= tol and b_vul > tol) else "FAIL"), f"selisih firing panel E = {b_env:.2e}; panel V = {b_vul:.2e}"),
        "H6c": ("PASS" if (c["pass"] and ident <= 1e-6) else "FAIL", f"rasio = {c['ratio']:.2f} (>= {args.ratio}); proporsi baris = {c['frac']:.3f} (>= {args.frac}); baris = {c['n_rows']}; degenerat = {c['n_degenerate']}; identitas kontribusi maks = {ident:.2e}"),
    }
    return res, c


# ----------------------------------------------------------------------------------------------------------------- main
def git_tags():
    try:
        return subprocess.run(["git", "tag", "-l", "e6-prereg-*"], capture_output=True, text=True, check=True).stdout.split()
    except Exception:
        return []


def main(argv=None, adapters32=None, adapters64=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--smoke", action="store_true"); g.add_argument("--run", action="store_true")
    ap.add_argument("--k", type=int, default=3); ap.add_argument("--ratio", type=float, default=2.0); ap.add_argument("--frac", type=float, default=0.90)
    ap.add_argument("--ndraw", type=int, default=100); ap.add_argument("--rand-seed", type=int, default=20261007)
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    rng = np.random.default_rng(args.rand_seed)
    if args.run and not git_tags():
        print("STATUS=HOLD_E6_PREREG_NOT_FROZEN  (tag git e6-prereg-* belum ada; bekukan praregistrasi E6 lebih dulu)")
        return 2
    meta = json.load(open(root / MODELS_DIR / META_FILE))
    table = pd.read_csv(root / TABLE)
    preds = pd.read_csv(root / MODELS_DIR / PRED_FILE)
    df, X = build_inputs(table, meta)
    a32 = adapters32 if adapters32 is not None else load_torch_adapters(root, meta, False)
    rep = replicate(a32, df, X, preds, exclude_p0if=args.smoke)
    print("== replikasi prediksi E4 dari model tersimpan (float32; baris P0-IF" + (" dikecualikan) ==" if args.smoke else " disertakan) =="))
    for f, r in rep.items():
        print(f"  fold {f}: agregasi={r['agregasi']} skala={r['skala']:g} maks|selisih|={r['maks_selisih']:.3e} n={r['n']} (NaN dibuang: {r['n_nan']})")
    rep_ok = all(r["maks_selisih"] <= 1e-3 for r in rep.values())
    a64 = adapters64 if adapters64 is not None else load_torch_adapters(root, meta, True)
    if args.smoke:
        idx = {e: i for i, e in enumerate(df["event_id"])}
        key0 = sorted(a64)[0]
        ad = a64[key0]
        sub = preds[(preds["fold"] == key0[0]) & ~preds["event_id"].str.contains("p0if", case=False)]
        Xt = X[[idx[e] for e in sub["event_id"]]]; Xt = Xt[~np.isnan(Xt).any(1)]
        h0 = h6_0(ad, Xt); idn = identity_checks(ad, Xt)
        print(f"== sifat fungsi pada baris non-P0-IF (model fold {key0[0]} seed {key0[1]}, N={len(Xt)}) ==\n  H6-0 (jejak vs inferensi): {h0}\n  identitas kontribusi: {idn}")
        Xs = np.random.default_rng(1).random((64, 7))
        _ = h6c(ad, Xs, args.k, 5, np.random.default_rng(2))
        print("  jalur kode H6c: dieksekusi pada masukan sintetis (nilai sengaja tidak dilaporkan)")
        ok = rep_ok and max(h0.values()) <= 1e-6 and max(idn.values()) <= 1e-6
        print("STATUS=E6_SMOKE_PASS" if ok else "STATUS=E6_SMOKE_HOLD")
        return 0 if ok else 2
    # --- run penuh
    out = analyse(a64, df, X, preds, meta, args, rng)
    res, c = decide(out, args)
    print("== Tahap 0 ==", json.dumps(out["tahap0"], ensure_ascii=False))
    print("== keputusan ==")
    for k, (st, note) in res.items():
        print(f"  {k:7} {st:24} {note}")
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    outp = root / OUT_DIR
    outp.mkdir(parents=True, exist_ok=True)
    keep = {k: v for k, v in out.items() if k != "h6c_parts"}
    keep.update({"keputusan": {k: list(v) for k, v in res.items()}, "h6c": c, "replikasi": rep, "args": vars(args), "tags": git_tags()})
    (outp / f"e6_results_{stamp}.json").write_text(json.dumps(keep, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"STATUS=E6_RUN_DONE ({outp}/e6_results_{stamp}.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
