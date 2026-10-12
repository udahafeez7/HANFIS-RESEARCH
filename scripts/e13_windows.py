#!/usr/bin/env python
"""E13 -- karakteristik operasi desain E7 pada jendela 6 minggu historis (POST HOC, deskriptif; tidak melatih apa pun).
Memakai prediksi out-of-fold E11 (event_id, image_id, y_true, y_maxform, y_pers, y_full). Untuk setiap jendela 6 minggu berurutan dihitung keputusan P7a, P7b (keluarga lama), P7e, P7f (rumus) dengan bootstrap per image yang sama seperti E7
(p satu sisi dengan +1; Holm alpha satu sisi 0,025), di bawah tiga susunan: (1) P7e dan P7f sekunder tanpa koreksi, (2) satu keluarga Holm berisi empat, (3) dua keluarga Holm terpisah {P7a,P7b} dan {P7e,P7f}.
Jendela saling tumpang tindih (sekitar 7 jendela bebas dari 45 minggu): angkanya deskriptif, bukan probabilitas formal.  python scripts/e13_windows.py [--pred results_python/e11/e11_predictions_*.csv]"""
import argparse, datetime as dt, glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("--pred", default="results_python/e11/e11_predictions_*.csv"); ap.add_argument("--lambda-json", default="protocols/E7_lambda_2026-10-08.json")
ap.add_argument("--weeks", type=int, default=6); ap.add_argument("--boot", type=int, default=1000); ap.add_argument("--seed", type=int, default=20261012); ap.add_argument("--recent-from", default="2026-06-15"); ap.add_argument("--out-dir", default="results_python/e13"); a = ap.parse_args()
SESOI, ALPHA = 0.05, 0.025
fs = sorted(glob.glob(a.pred)); M = pd.read_csv(fs[-1]) if fs else sys.exit(f"ABORT: tidak ada berkas {a.pred}")
lam = json.load(open(a.lambda_json))["lambda"]; M["week"] = M["event_id"].str.rsplit("__", n=1).str[1]; M["grup"] = M["image_id"].str.replace(r"-(on|off)$", "", regex=True)
M["y_hib"] = lam * M["y_full"] + (1 - lam) * M["y_pers"]; weeks = sorted(M["week"].unique()); wd = [dt.date.fromisoformat(w) for w in weeks]
print(f"berkas {fs[-1]} | baris {len(M)} | minggu {len(weeks)} ({weeks[0]} .. {weeks[-1]}) | lambda {lam:.4f}")


def holm(ps):
    order = sorted(ps, key=ps.get); out, m, stop = {}, len(order), False
    for i, k in enumerate(order):
        thr = ALPHA / (m - i); ok = (not stop) and ps[k] <= thr; out[k] = ok; stop = stop or not ok
    return out


def one_window(g, rng):
    groups = sorted(g["grup"].unique()); gi = {x: i for i, x in enumerate(groups)}; idx = g["grup"].map(gi).to_numpy(); G = len(groups); cnt = rng.multinomial(G, np.full(G, 1.0 / G), size=a.boot); y = g["y_true"].to_numpy(); S = {}
    for c in ("y_pers", "y_full", "y_hib", "y_maxform"): v = np.zeros(G); np.add.at(v, idx, (g[c].to_numpy() - y) ** 2); S[c] = v
    def ss(m, b): bs = 1 - (cnt @ S[m]) / (cnt @ S[b]); return 1 - S[m].sum() / S[b].sum(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), bs
    A, B, E, F = ss("y_full", "y_pers"), ss("y_hib", "y_pers"), ss("y_maxform", "y_pers"), ss("y_full", "y_maxform"); n = a.boot + 1
    p = {"a": (1 + int((A[3] >= SESOI).sum())) / n, "b": (1 + int((B[3] <= 0).sum())) / n, "e": (1 + int((E[3] <= 0).sum())) / n, "f": (1 + int((F[3] >= SESOI).sum())) / n}
    return {"a": A[:3], "b": B[:3], "e": E[:3], "f": F[:3]}, p


def decide(k, st, ok):
    ss_, lo, hi = st
    if k == "a": return "DIDUKUNG" if (hi < SESOI and ok) else ("DIBANTAH" if (ss_ >= SESOI and lo > 0) else "TIDAK TERBUKTI")
    if k == "f": return "DIDUKUNG" if (hi < SESOI and ok) else ("DIBANTAH" if (ss_ >= SESOI and lo > 0) else "TIDAK TERBUKTI")
    return "TERKONFIRMASI" if (ss_ >= SESOI and lo > 0 and ok) else ("LEBIH BURUK" if hi < 0 else "TIDAK TERKONFIRMASI")


rng = np.random.default_rng(a.seed); rows, skipped = [], 0
for i in range(0, len(weeks) - a.weeks + 1):
    if any((wd[i + j + 1] - wd[i + j]).days != 7 for j in range(a.weeks - 1)): skipped += 1; continue
    g = M[M["week"].isin(weeks[i:i + a.weeks])]; st, p = one_window(g, rng); h12 = holm({k: p[k] for k in ("a", "b")}); h34 = holm({k: p[k] for k in ("e", "f")}); h4 = holm(p)
    r = {"inicio": weeks[i], "fim": weeks[i + a.weeks - 1], "baris": len(g), "recente": wd[i] >= dt.date.fromisoformat(a.recent_from)}
    for k in "abef": r[f"ss_{k}"] = round(float(st[k][0]), 3); r[f"ci_{k}"] = f"[{st[k][1]:+.2f},{st[k][2]:+.2f}]"; r[f"p_{k}"] = round(p[k], 4)
    for opt, oks in (("o1", {"a": h12["a"], "b": h12["b"], "e": True, "f": True}), ("o2", h4), ("o3", {**h12, **h34})):
        for k in "abef": r[f"{opt}_{k}"] = decide(k, st[k], oks[k])
    rows.append(r)
W = pd.DataFrame(rows); print(f"CATATAN: minggu berformat ISO ({weeks[0]}); jendela 'recent' = awal >= {a.recent_from} (dibandingkan sebagai tanggal)")
print(f"jendela {a.weeks} minggu: {len(W)} (dilewati karena celah kalender: {skipped}); jendela dengan awal >= {a.recent_from} (model EPSS baru): {int(W.recente.sum())}")
if W.empty: sys.exit("ABORT: tidak ada jendela berurutan")
frac = lambda d, k, lab: f"{100 * (d[k] == lab).mean():5.0f}%"
for name, d in (("SEMUA jendela", W), ("jendela RECENT (model EPSS baru)", W[W.recente])):
    if d.empty: continue
    print(f"\n== {name} (n={len(d)}) ==")
    print(f"   SS median (rerata kena ekor berat): HANFIS {d.ss_a.median():+.3f} | hibrida {d.ss_b.median():+.3f} | rumus {d.ss_e.median():+.3f} | HANFIS vs rumus {d.ss_f.median():+.3f}")
    print("   susunan | P7a DIDUKUNG | P7b TERKONFIRMASI | P7e TERKONFIRMASI | P7f DIDUKUNG")
    for opt, lab in (("o1", "(1) sekunder"), ("o2", "(2) Holm 4   "), ("o3", "(3) 2 keluarga")): print(f"   {lab} | {frac(d, opt + '_a', 'DIDUKUNG'):>12} | {frac(d, opt + '_b', 'TERKONFIRMASI'):>17} | {frac(d, opt + '_e', 'TERKONFIRMASI'):>17} | {frac(d, opt + '_f', 'DIDUKUNG'):>11}")
    blk = ((d.o1_a != d.o2_a) | (d.o1_b != d.o2_b)).mean() * 100; print(f"   keputusan P7a atau P7b yang BERUBAH bila memakai Holm 4 (pengikatan): {blk:.0f}% jendela")
od = Path(a.out_dir); od.mkdir(parents=True, exist_ok=True); stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"); W.to_csv(od / f"e13_windows_{stamp}.csv", index=False); print(f"\nSTATUS=E13_DONE ({od}/e13_windows_{stamp}.csv)")
