#!/usr/bin/env python3
"""E7 -- pemeriksa kesiapan pembekuan (HANYA MEMBACA; tidak membuat tag, tidak mengubah berkas apa pun).
Memeriksa: (1) kurung siku placeholder yang masih ada di protokol, (2) setiap artefak beku (daftar yang sama dengan scripts/e7_d2.py) ada, terlacak git, bersih (tidak berubah), dan disebut di bagian 8 protokol,
(3) hash SHA256 yang perlu diisi di protokol, (4) skrip beku lulus uji sintaks. Cetak STATUS=E7_FREEZE_READY atau STATUS=HOLD_E7_FREEZE_NOT_READY dengan alasannya.
  python scripts/e7_freeze_check.py [--protocol protocols/E7_preregistration_CANDIDATE.md] [--date 2026-10-20]"""
import argparse, ast, hashlib, importlib.util, re, subprocess, sys
from pathlib import Path

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("--protocol", default="protocols/E7_preregistration_CANDIDATE.md"); ap.add_argument("--date", default=None); ap.add_argument("--root", default="."); a = ap.parse_args()
root = Path(a.root).resolve(); problems, notes = [], []
sh = lambda *c: subprocess.run(["git", *c], cwd=root, capture_output=True, text=True)
sha = lambda p: hashlib.sha256((root / p).read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location("e7_d2", root / "scripts" / "e7_d2.py"); d2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(d2)
prot = root / a.protocol
if not prot.exists(): print(f"ABORT: {a.protocol} tidak ada"); sys.exit(2)
text = prot.read_text(encoding="utf-8")
# 1) placeholder
ph = [(i + 1, m) for i, line in enumerate(text.split("\n")) for m in re.findall(r"\[[A-Z][A-Z0-9 ]{2,}\]", line) if m not in ("[KURUNG SIKU]", "[KEV]")]  # [KEV] = indikator 1[KEV] di rumus label, bukan placeholder
print(f"== 1. placeholder di {a.protocol}: {len(ph)} ==")
for ln, m in ph[:30]: print(f"   baris {ln}: {m}")
if ph: problems.append(f"{len(ph)} placeholder belum diisi (isi saat pembekuan, bagian 11 langkah 1)")
# 2) artefak
models = sorted(str(p.relative_to(root)) for p in (root / "results_python/e7_final/models").glob("final_seed*_hanfis.pt"))
frozen = list(d2.STATIC) + models; sec8 = re.search(r"^## 8\..*?(?=^## 9\.)", text, re.S | re.M); sec8 = sec8.group(0) if sec8 else ""
print(f"== 2. artefak beku ({len(frozen)} + protokol): ada / git-terlacak / bersih / disebut di bagian 8 ==")
if len(models) != 5: problems.append(f"model akhir: {len(models)} berkas final_seed*_hanfis.pt (harus 5)")
for p in frozen:
    ex = (root / p).exists(); tr = ex and sh("ls-files", "--error-unmatch", p).returncode == 0; cl = tr and sh("status", "--porcelain", "--", p).stdout.strip() == ""
    mentioned = (p in sec8) or ("final_seed*_hanfis.pt" in sec8 and p in models) or (p.startswith("results_python/e7_final") and "results_python/e7_final" in sec8)
    flag = "OK " if (ex and tr and cl and mentioned) else "!! "; print(f"   {flag}{p:62} ada={ex!s:5} terlacak={tr!s:5} bersih={cl!s:5} bagian8={mentioned}")
    if not ex: problems.append(f"{p}: tidak ada")
    elif not tr: problems.append(f"{p}: belum terlacak git (git add -f bila di folder yang diabaikan)")
    elif not cl: problems.append(f"{p}: ada perubahan yang belum dikomit")
    if ex and not mentioned: problems.append(f"{p}: tidak disebut di bagian 8 protokol")
pn = a.protocol; tr = sh("ls-files", "--error-unmatch", pn).returncode == 0; cl = tr and sh("status", "--porcelain", "--", pn).stdout.strip() == ""
print(f"   protokol {pn}: terlacak={tr}, bersih={cl}")
if not (tr and cl): problems.append("protokol belum dikomit atau berubah")
# 3) hash untuk placeholder
print("== 3. SHA256 untuk diisi di protokol ==")
for p in ("results_python/e7_final/final_models_manifest.json", "protocols/E7_lambda_2026-10-08.json", d2.FORMULA, "data/real/snapshots/manifest.json"):
    print(f"   {p}: {sha(p) if (root / p).exists() else 'TIDAK ADA'}")
print("   (manifest.json snapshot dicatat hash-nya di protokol tetapi TIDAK ada di daftar verifikasi: ia berubah saat snapshot baru ditarik setelah tag)")
base = sh("rev-parse", "--short", "HEAD").stdout.strip(); print(f"   komit dasar sekarang: {base} (isi [HASH KOMIT] dengan hash komit INDUK dari komit pembekuan; protokol tidak dapat memuat hash komitnya sendiri)")
# 4) sintaks
bad = []
for p in frozen:
    if p.endswith(".py") and (root / p).exists():
        try: ast.parse((root / p).read_text(encoding="utf-8"))
        except SyntaxError as e: bad.append(f"{p}: {e}")
print(f"== 4. sintaks skrip beku: {'OK' if not bad else bad} ==")
problems += bad
# 5) faixas de configs/assets.csv (contrato: criticality 1..5, mfa/exposure/rho 0..1); build_asset_weeks.py gagal-tertutup (FAIL_CONTRACT) bila ada pelanggaran
try:
    import pandas as pd
    A = pd.read_csv(root / "configs" / "assets.csv"); viol = []
    for col, lo, hi in (("asset_criticality", 1, 5), ("mfa_risk", 0, 1), ("kubernetes_exposure", 0, 1), ("default_rho", 0, 1)):
        bad_ = A[(A[col] < lo) | (A[col] > hi) | A[col].isna()]
        viol += [f"{r.asset_id}: {col} = {getattr(r, col)} di luar [{lo},{hi}]" for r in bad_.itertuples()]
    print(f"== 5. faixa nilai configs/assets.csv ({len(A)} aset): {'OK' if not viol else str(len(viol)) + ' pelanggaran'} ==")
    for v in viol[:12]: print("   !!", v)
    if viol: problems.append(f"configs/assets.csv: {len(viol)} nilai di luar kontrak (build D2 akan FAIL_CONTRACT); contoh: {viol[0]}")
except Exception as ex: print(f"== 5. configs/assets.csv tidak dapat diperiksa: {ex} =="); problems.append(f"configs/assets.csv tidak dapat diperiksa: {ex}")
head = sh("log", "--oneline", "-1").stdout.strip(); dirty = [l for l in sh("status", "--porcelain").stdout.split("\n") if l and not l.startswith("??")]
print(f"== HEAD: {head}; berkas terlacak yang berubah di pohon kerja: {len(dirty)} ==")
if problems:
    print("\nSTATUS=HOLD_E7_FREEZE_NOT_READY"); [print("  -", p) for p in problems]; sys.exit(1)
if a.date:
    print("\nPerintah tag (setelah berkas protokol diganti nama dan dikomit):\n  python scripts/make_prereg_tag.py e7-prereg-" + a.date + " protocols/E7_preregistration_" + a.date + ".md " + " ".join(frozen))
print("\nSTATUS=E7_FREEZE_READY (setelah placeholder terisi dan komit; tag dibuat oleh make_prereg_tag.py, bukan skrip ini)")
