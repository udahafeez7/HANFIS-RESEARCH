#!/usr/bin/env python3
"""E7 -- rumus bentuk-maks sebagai pembanding terdaftar (tambahan protokol; hipotesis SEKUNDER P7e dan P7f, tanpa koreksi multiplisitas, dilaporkan dengan CI). Tidak menyentuh e7_pipeline.py maupun e7_evaluate.py.
  fit      : memasang  y_hat = a + b * max(x2, c * x7)  pada baris latih yang SAMA dengan model akhir (berlabel, minggu <= cutoff), c dari grid 0..1,5 (langkah 0,05), a dan b dengan OLS; menulis JSON beku.
  evaluate : pada prediksi forward (kolom event_id, y_true, y_hanfis, y_lag4) dan tabel v3 (kolom event_id, exploitability, threat_intelligence), memakai populasi dan bootstrap berkelompok per image yang sama
             dengan e7_evaluate.py (2.000 resampel, seed 20261102).  P7e: rumus lebih baik dari persistence (SS >= 0,05 dan batas bawah CI95 > 0 -> TERKONFIRMASI; batas atas < 0 -> LEBIH BURUK; selain itu TIDAK TERKONFIRMASI).
             P7f: HANFIS tidak lebih baik dari rumus (batas atas CI95 SS_HANFIS-terhadap-rumus < 0,05 -> DIDUKUNG; SS >= 0,05 dan batas bawah > 0 -> DIBANTAH; selain itu TIDAK TERBUKTI).
             --run menolak berjalan kecuali verify_prereg_tag.py LOLOS dan menolak bila hasil resmi sudah ada (SEKALI); --rehearsal menguji jalur kode pada berkas mana saja (BUKAN hasil E7).
  python scripts/e7_formula.py fit [--table ... --cutoff 2026-07-27 --expect-rows 5880 --out protocols/E7_formula_2026-10-12.json]
  python scripts/e7_formula.py evaluate --run --pred P.csv --table asset_weeks_v3.csv --formula-json F.json --tag TAG --files ..."""
import argparse, datetime as dt, glob, hashlib, json, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd

SESOI, MIN_WEEKS, FORMULA, GRID = 0.05, 6, "protocols/E7_formula_2026-10-12.json", np.round(np.arange(0.0, 1.5001, 0.05), 2)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def feats(df):
    return df["exploitability"].fillna(0.0).to_numpy(float), df["threat_intelligence"].fillna(0.0).to_numpy(float)


def predict(x2, x7, f):
    return f["a"] + f["b"] * np.maximum(x2, f["c"] * x7)


def do_fit(a):
    df = pd.read_csv(a.table); df["w"] = pd.to_datetime(df["week_start_utc"], utc=True).dt.strftime("%Y-%m-%d"); tr = df[df["y"].notna() & (df["w"] <= a.cutoff)]
    if a.expect_rows and len(tr) != a.expect_rows: print(f"ABORT: {len(tr)} baris latih, diharapkan {a.expect_rows} (sama dengan model akhir); tidak ada yang ditulis"); return 2
    x2, x7 = feats(tr); y = tr["y"].to_numpy(float); best = None
    for c in GRID:
        A = np.c_[np.ones(len(y)), np.maximum(x2, c * x7)]; coef = np.linalg.lstsq(A, y, rcond=None)[0]; sse = float(((A @ coef - y) ** 2).sum())
        if best is None or sse < best[0]: best = (sse, float(c), coef)
    out = {"formula": "a + b * max(x2, c * x7); x2 = exploitability, x7 = threat_intelligence (nilai hilang = 0)", "a": float(best[2][0]), "b": float(best[2][1]), "c": best[1], "n_train": int(len(tr)), "cutoff": a.cutoff,
           "mse_train": best[0] / len(tr), "table": str(a.table), "table_sha256": sha(a.table), "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    p = Path(a.out)
    if p.exists(): print(f"ABORT: {p} sudah ada (dibekukan; tidak ditimpa)"); return 2
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, indent=1)); print(json.dumps({k: out[k] for k in ("a", "b", "c", "n_train", "mse_train")})); print(f"STATUS=E7_FORMULA_FIT_DONE ({p})"); return 0


def boot(df, pairs, B, seed):
    groups = sorted(df["grup"].unique()); gi = {g: i for i, g in enumerate(groups)}; idx = df["grup"].map(gi).to_numpy(); G = len(groups); sse = {}
    for c in {c for p in pairs for c in p}:
        v = np.zeros(G); np.add.at(v, idx, (df[c].to_numpy() - df["y_true"].to_numpy()) ** 2); sse[c] = v
    cnt = np.random.default_rng(seed).multinomial(G, np.full(G, 1.0 / G), size=B); out = {}
    for m, base in pairs:
        bs = 1.0 - (cnt @ sse[m]) / (cnt @ sse[base]); out[(m, base)] = {"ss": float(1.0 - sse[m].sum() / sse[base].sum()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                                                                       "mse_m": float(sse[m].sum() / len(df)), "mse_base": float(sse[base].sum() / len(df))}
    return out


def do_eval(a, verifier=None):
    if a.run:
        if not a.tag or not a.files: print("ABORT: --run memerlukan --tag dan --files"); return 2
        r = verifier() if verifier else subprocess.run([sys.executable, str(Path(__file__).with_name("verify_prereg_tag.py")), a.tag, *a.files], capture_output=True, text=True)
        if not (r if isinstance(r, bool) else r.returncode == 0): print("STATUS=HOLD_E7_PREREG_NOT_VERIFIED"); return 2
        if glob.glob(str(Path(a.out_dir) / "e7_formula_results_*.json")): print("STATUS=HOLD_E7_FORMULA_ALREADY_RUN (dijalankan SEKALI; hasil sudah ada)"); return 2
    f = json.load(open(a.formula_json)); df = pd.read_csv(a.pred); need = {"event_id", "y_true", "y_hanfis", "y_lag4"}
    if not need <= set(df.columns): print(f"ABORT: kolom kurang: {sorted(need - set(df.columns))}"); return 2
    df["week"] = df["event_id"].str.rsplit("__", n=1).str[1]; df = df.dropna(subset=list(need - {"event_id"})).copy()
    df["grup"] = df["event_id"].str.rsplit("__", n=1).str[0].str.replace(r"-(on|off)$", "", regex=True)
    t = pd.read_csv(a.table, usecols=["event_id", "exploitability", "threat_intelligence"]).drop_duplicates("event_id"); df = df.merge(t, on="event_id", how="left", validate="many_to_one")
    if "exploitability" not in df or df["event_id"].isin(t["event_id"]).sum() != len(df): print("ABORT: ada baris prediksi tanpa padanan di tabel v3"); return 2
    x2, x7 = feats(df); df["y_formula"] = predict(x2, x7, f); weeks = sorted(df["week"].unique())
    if len(weeks) < MIN_WEEKS: print(f"STATUS=HOLD_E7_TOO_FEW_WEEKS ({len(weeks)} < {MIN_WEEKS})"); return 3
    r = boot(df, [("y_formula", "y_lag4"), ("y_hanfis", "y_formula"), ("y_hanfis", "y_lag4")], a.boot, a.seed); e, h = r[("y_formula", "y_lag4")], r[("y_hanfis", "y_formula")]
    v_e = "TERKONFIRMASI" if (e["ss"] >= SESOI and e["ci95"][0] > 0) else ("LEBIH BURUK" if e["ci95"][1] < 0 else "TIDAK TERKONFIRMASI")
    v_f = "DIDUKUNG" if h["ci95"][1] < SESOI else ("DIBANTAH" if (h["ss"] >= SESOI and h["ci95"][0] > 0) else "TIDAK TERBUKTI")
    out = {"mode": "REHEARSAL (bukan hasil E7)" if a.rehearsal else "RUN", "formula": {k: f[k] for k in ("a", "b", "c", "n_train", "cutoff")}, "minggu": len(weeks), "baris": int(len(df)), "kelompok": int(df["grup"].nunique()),
           "P7e_rumus_vs_persistence": {**e, "keputusan": v_e}, "P7f_hanfis_vs_rumus": {**h, "keputusan": v_f}, "deskriptif_hanfis_vs_persistence": r[("y_hanfis", "y_lag4")], "catatan": "sekunder; tanpa koreksi multiplisitas"}
    od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=True); stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"); fp = od / f"e7_formula_{'rehearsal' if a.rehearsal else 'results'}_{stamp}.json"
    fp.write_text(json.dumps(out, indent=1)); print(f"{out['mode']}: {len(weeks)} minggu, {len(df)} baris")
    print(f"P7e rumus vs persistence: SS {e['ss']:+.3f} [{e['ci95'][0]:+.3f}, {e['ci95'][1]:+.3f}] -> {v_e}"); print(f"P7f HANFIS vs rumus: SS {h['ss']:+.3f} [{h['ci95'][0]:+.3f}, {h['ci95'][1]:+.3f}] -> {v_f}"); print(f"STATUS=E7_FORMULA_DONE ({fp})"); return 0


def main(argv=None, verifier=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit"); f.add_argument("--table", default="data/processed/asset_weeks_v2_120assets_e4bis.csv"); f.add_argument("--cutoff", default="2026-07-27"); f.add_argument("--expect-rows", type=int, default=5880); f.add_argument("--out", default=FORMULA)
    e = sub.add_parser("evaluate"); g = e.add_mutually_exclusive_group(required=True); g.add_argument("--rehearsal", action="store_true"); g.add_argument("--run", action="store_true")
    e.add_argument("--pred", required=True); e.add_argument("--table", required=True); e.add_argument("--formula-json", default=FORMULA); e.add_argument("--tag"); e.add_argument("--files", nargs="*", default=[])
    e.add_argument("--boot", type=int, default=2000); e.add_argument("--seed", type=int, default=20261102); e.add_argument("--out-dir", default="results_python/e7"); a = ap.parse_args(argv)
    return do_fit(a) if a.cmd == "fit" else do_eval(a, verifier)


if __name__ == "__main__":
    sys.exit(main())
