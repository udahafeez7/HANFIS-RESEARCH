#!/usr/bin/env python3
r"""Mengganti frasa ambigu 'contribution to the network architecture' pada pernyataan kontribusi B.R. (Dr. Budi Rahmadya) di manuscript/sn-article.tex.
Dua pilihan kata (pilih yang sesuai dengan kontribusi sebenarnya; konfirmasi Dr. Budi dahulu):
  --variant testbed : contribution to the design of the experimental platform (cluster and telemetry network)
  --variant model   : contribution to the architecture of the HANFIS model
Gagal-tertutup: tepat satu keadaan (asli, testbed, atau model) harus ada tepat sekali; tidak ada yang ditulis bila tidak. Idempoten; boleh berpindah pilihan. Cadangan .pre-budi.bak.
   python scripts/apply_author_budi.py --variant testbed|model [--tex manuscript/sn-article.tex]"""
import argparse, shutil, sys
from pathlib import Path
PRE, POST = "B.R.: supervision, ", ", methodology review, writing -- review and editing."
STATES = {"orig": "contribution to the network architecture",
          "testbed": "contribution to the design of the experimental platform (cluster and telemetry network)",
          "model": "contribution to the architecture of the HANFIS model"}
ap = argparse.ArgumentParser(); ap.add_argument("--variant", required=True, choices=["testbed", "model"]); ap.add_argument("--tex", default="manuscript/sn-article.tex"); a = ap.parse_args()
P = Path(a.tex); s = P.read_text(encoding="utf-8")
found = {k: s.count(PRE + v + POST) for k, v in STATES.items()}
present = [k for k, n in found.items() if n == 1]
if len(present) != 1 or sum(found.values()) != 1: sys.exit(f"ABORT, tidak ada yang ditulis: keadaan ditemukan {found} (harus tepat satu, sekali)")
cur = present[0]
if cur == a.variant: print("Tidak ada perubahan (sudah sama)."); sys.exit(0)
new = s.replace(PRE + STATES[cur] + POST, PRE + STATES[a.variant] + POST, 1)
shutil.copy(P, str(P) + ".pre-budi.bak"); P.write_text(new, encoding="utf-8"); print(f"OK: B.R. {cur} -> {a.variant}")
