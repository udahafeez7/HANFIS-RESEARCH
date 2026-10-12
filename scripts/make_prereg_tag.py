#!/usr/bin/env python3
"""Buat tag pembekuan HANYA bila setiap berkas sudah dilacak dan dikomit tanpa perubahan, lalu verifikasi dengan verify_prereg_tag.py.
Pelajaran E6: `git tag` setelah `git commit` yang gagal membekukan komit LAMA. Skrip ini menolak membuat tag dalam keadaan itu.
  python scripts/make_prereg_tag.py <tag> <berkas> [<berkas> ...]        (keluar 0 bila tag dibuat dan LOLOS verifikasi; selain itu 2)"""
import subprocess, sys
from pathlib import Path

def git(*a):
    r = subprocess.run(["git", *a], capture_output=True, text=True); return r.returncode, r.stdout.strip()

def main(argv):
    if len(argv) < 2: print(__doc__); return 2
    tag, files = argv[0], argv[1:]; bad = []
    if git("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}")[0] == 0: print(f"GAGAL: tag {tag} sudah ada (tag tidak dipindahkan)"); return 2
    for f in files:
        if git("ls-files", "--error-unmatch", f)[0]: bad.append(f"{f}: tidak dilacak git (git add dan git commit dulu)"); continue
        rc, out = git("status", "--porcelain", "--", f)
        if out: bad.append(f"{f}: ada perubahan yang belum dikomit")
    if bad:
        print("GAGAL, tag TIDAK dibuat:"); [print("  -", b) for b in bad]; return 2
    rc, head = git("rev-parse", "--short", "HEAD")
    if git("tag", "-a", tag, "-m", f"prereg freeze {tag}")[0]: print("GAGAL: git tag gagal"); return 2
    print(f"tag {tag} dibuat pada HEAD {head}")
    return subprocess.run([sys.executable, str(Path(__file__).with_name("verify_prereg_tag.py")), tag, *files]).returncode

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
