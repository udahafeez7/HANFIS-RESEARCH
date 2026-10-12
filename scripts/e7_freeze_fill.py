#!/usr/bin/env python3
"""E7 -- pengisi placeholder pembekuan (mengurangi salin-tempel hash manual). Dua tahap:
  --stage protocol --date YYYY-MM-DD : (1) git mv protokol kandidat -> protocols/E7_preregistration_<tanggal>.md, (2) mengisi [TANGGAL], [HASH KOMIT] (= komit INDUK, yaitu HEAD saat ini), [TAG], [SHA256 MANIFES], [SHA256] (lambda, rumus, manifest snapshot),
     (3) mengganti 'KANDIDAT' menjadi 'BEKU'. Setiap pengganti harus cocok tepat sekali; sisa placeholder = ABORT. Tidak membuat komit atau tag.
  --stage osf --date YYYY-MM-DD      : SETELAH tag ada: mengisi [HASH LIST], [FORMULA HASH], [COMMIT HASH], [TAG], [DATE/TIME +0700] di teks OSF dari tag yang sebenarnya.
  --dry-run mencetak apa yang akan diganti tanpa menulis.  Dari akar repo."""
import argparse, datetime as dt, hashlib, re, subprocess, sys
from pathlib import Path
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("--stage", choices=["protocol", "osf"], required=True); ap.add_argument("--date", required=True)
ap.add_argument("--protocol", default="protocols/E7_preregistration_CANDIDATE.md"); ap.add_argument("--osf", default="protocols/E7_osf_registration_DRAFT.md"); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
try: dt.date.fromisoformat(a.date)
except ValueError: sys.exit("ABORT: --date harus YYYY-MM-DD")
git = lambda *c: subprocess.run(["git", *c], capture_output=True, text=True); tag = f"e7-prereg-{a.date}"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
H = {"manifest": "results_python/e7_final/final_models_manifest.json", "lambda": "protocols/E7_lambda_2026-10-08.json", "formula": "protocols/E7_formula_2026-10-12.json", "snap": "data/real/snapshots/manifest.json"}
for k, p in H.items():
    if not Path(p).exists(): sys.exit(f"ABORT: {p} tidak ada")


def apply(s, subs):
    for rx, new, expect in subs:
        n = len(re.findall(rx, s))
        if expect == 1 and n != 1: sys.exit(f"ABORT, tidak ada yang ditulis: pola '{rx[:60]}' ditemukan {n}x (harus 1)")
        if expect == "+" and n < 1: sys.exit(f"ABORT, tidak ada yang ditulis: pola '{rx[:60]}' tidak ditemukan")
        s = re.sub(rx, new, s)
    return s


if a.stage == "protocol":
    src = Path(a.protocol); dst = Path(f"protocols/E7_preregistration_{a.date}.md")
    if not src.exists(): sys.exit(f"ABORT: {src} tidak ada")
    if dst.exists(): sys.exit(f"ABORT: {dst} sudah ada")
    base = git("rev-parse", "--short", "HEAD").stdout.strip(); s = src.read_text(encoding="utf-8")
    s = apply(s, [(r"Tanggal pembekuan: \[TANGGAL\]\. Komit: \[HASH KOMIT\]\. Tag: \[TAG\]\.", f"Tanggal pembekuan: {a.date}. Komit dasar (induk komit pembekuan): {base}. Tag: {tag}.", 1),
                  (r"(`results_python/e7_final/final_models_manifest\.json`) \[SHA256 MANIFES\]", rf"\1 (SHA256 {sha(H['manifest'])})", 1),
                  (r"(`protocols/E7_lambda_2026-10-08\.json`) \[SHA256\]", rf"\1 (SHA256 {sha(H['lambda'])})", 1),
                  (r"(`protocols/E7_formula_2026-10-12\.json`) \[SHA256\]", rf"\1 (SHA256 {sha(H['formula'])})", 1),
                  (r"(`data/real/snapshots/manifest\.json`) \[SHA256\]", rf"\1 (SHA256 {sha(H['snap'])}, keadaan saat pembekuan; berkas ini berubah setelah snapshot baru ditarik)", 1),
                  (r"\[TANGGAL\]", a.date, "+"), (r"\*\*Status: KANDIDAT\.\*\*", "**Status: BEKU.**", 1), (r"\(KANDIDAT PEMBEKUAN, satu dokumen konsisten\)", "(BEKU, satu dokumen konsisten)", 1)])
    left = [m for m in re.findall(r"\[[A-Z][A-Z0-9 ]{2,}\]", s) if m not in ("[KEV]", "[KURUNG SIKU]")]
    if left: sys.exit(f"ABORT: placeholder tersisa: {sorted(set(left))}")
    print(f"komit dasar (induk): {base}; tag: {tag}; berkas baru: {dst}")
    if a.dry_run: print("--dry-run: tidak ada yang ditulis"); sys.exit(0)
    if git("ls-files", "--error-unmatch", str(src)).returncode == 0: git("mv", str(src), str(dst))
    else: src.rename(dst)
    dst.write_text(s, encoding="utf-8"); print(f"OK: {dst} terisi. Berikutnya: git add -f results_python/e7_final; git add {dst} (dan git rm sisa kandidat bila perlu); python scripts/e7_freeze_check.py --date {a.date}; komit; make_prereg_tag.py")
else:
    if git("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}").returncode != 0: sys.exit(f"ABORT: tag {tag} belum ada; tahap osf dijalankan SETELAH tag dibuat")
    p = Path(a.osf); s = p.read_text(encoding="utf-8"); commit = git("rev-list", "-n", "1", "--abbrev-commit", tag).stdout.strip()
    cd = dt.datetime.fromisoformat(git("for-each-ref", "--format=%(creatordate:iso-strict)", f"refs/tags/{tag}").stdout.strip()).astimezone(dt.timezone(dt.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S +0700")
    models = sorted(Path("results_python/e7_final/models").glob("final_seed*_hanfis.pt")); hl = "; ".join([f"manifest {sha(H['manifest'])}"] + [f"{m.name} {sha(m)}" for m in models])
    s2 = apply(s, [(r"\[HASH LIST\]", hl.replace("\\", "/"), 1), (r"\[FORMULA HASH\]", sha(H["formula"]), 1), (r"\[COMMIT HASH\]", commit, 1), (r"\[TAG\]", tag, 1), (r"\[DATE/TIME \+0700\]", cd, 1)])
    print(f"tag {tag} -> komit {commit}, dibuat {cd}; {len(models)} model")
    if a.dry_run: print("--dry-run: tidak ada yang ditulis"); sys.exit(0)
    p.write_text(s2, encoding="utf-8"); print(f"OK: {p} terisi dari tag yang sebenarnya")
