#!/usr/bin/env python3
"""Verifikasi bahwa tag pembekuan SUNGGUH memuat protokol dan skrip, dan isinya sama dengan berkas kerja. Pelajaran E6: tag dapat dibuat pada komit lama.
  python scripts/verify_prereg_tag.py <tag> <berkas> [<berkas> ...]      (keluar 0 bila semua lolos; selain itu 2)
Memeriksa: tag ada; tag adalah leluhur HEAD; setiap berkas ada di pohon tag; blob di tag == blob berkas kerja (sha1 git)."""
import subprocess, sys

def git(*a):
    r = subprocess.run(["git", *a], capture_output=True, text=True); return r.returncode, r.stdout.strip()

def main(argv):
    if len(argv) < 2: print(__doc__); return 2
    tag, files = argv[0], argv[1:]; bad = []
    rc, commit = git("rev-parse", "--verify", f"{tag}^{{commit}}")
    if rc: print(f"GAGAL: tag {tag} tidak ada"); return 2
    rc, _ = git("merge-base", "--is-ancestor", commit, "HEAD")
    if rc: bad.append("tag bukan leluhur HEAD")
    for f in files:
        rc, intag = git("rev-parse", f"{tag}:{f}")
        if rc: bad.append(f"{f}: TIDAK ADA di pohon tag"); continue
        rc, work = git("hash-object", f)
        if rc or work != intag: bad.append(f"{f}: isi di tag berbeda dari berkas kerja")
    if bad:
        print(f"GAGAL ({tag} -> {commit[:7]}):"); [print("  -", b) for b in bad]; return 2
    print(f"LOLOS: {tag} -> {commit[:7]} memuat {len(files)} berkas dengan isi identik dengan berkas kerja"); return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
