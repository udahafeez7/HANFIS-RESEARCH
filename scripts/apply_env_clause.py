#!/usr/bin/env python3
"""Tambal kecil di Discussion: tegaskan bahwa target tidak bergantung pada tiga masukan lingkungan, sehingga inventaris ini tidak dirancang untuk menunjukkan manfaatnya.
Menyisipkan satu kalimat sebelum 'A forward evaluation on weeks after the protocol was frozen is planned'. Jangkar fleksibel; gagal-tertutup (tepat 1); idempoten; cadangan .pre-env.bak."""
import re, shutil, sys
from pathlib import Path
P = Path("manuscript/sn-article.tex"); s = P.read_text(encoding="utf-8")
flex = lambda t: r"\s+".join(map(re.escape, t.split()))
SENT = ("Because the target is built from EPSS, KEV and reachability alone and does not depend on the three environmental inputs, this inventory is not designed to show a benefit of those inputs even if one exists; "
        "testing it requires an outcome that depends on the environment, such as incident or impact data. ")
if "is not designed to show a benefit of those inputs" in s: print("Sudah diterapkan."); sys.exit(0)
m = list(re.finditer(flex("A forward evaluation on weeks after the protocol was frozen is planned"), s))
if len(m) != 1: print(f"ABORT: jangkar ditemukan {len(m)}x (harus 1); tidak ada yang ditulis"); sys.exit(2)
shutil.copy(P, str(P) + ".pre-env.bak"); P.write_text(s[:m[0].start()] + SENT + s[m[0].start():], encoding="utf-8"); print("OK: kalimat ditambahkan di Discussion")
