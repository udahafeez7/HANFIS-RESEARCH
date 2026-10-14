#!/usr/bin/env python3
r"""Penyuntingan tahap 3 untuk manuscript/sn-article.tex: 11 suntingan.
  K1-K4 : rujukan yang hilang untuk hal yang dipakai naskah: Prometheus (prometheus_overview), bootstrap (efron1979bootstrap), koreksi Holm (holm1979simple), katalog CISA KEV (cisa_kev);
          keempat kunci sudah ada di manuscript/sn-bibliography.bib (ditambahkan 14 Okt, metadata diaudit).
  M1-M5 : kalimat Methods yang panjang atau rusak tata bahasanya dipecah, termasuk kalimat inventaris 78 kata yang kehilangan kata kerjanya (M1);
  T1-T2 : dua pola kontras 'rather than' di Results dihapus tanpa mengubah kekuatan klaim.
Terapkan SETELAH tahap 1 dan 2. Setiap suntingan hanya mengganti teks lama yang COCOK PERSIS dan muncul TEPAT SEKALI; yang tidak cocok DILEWATI dan dilaporkan; cocok lebih dari sekali membatalkan seluruh proses.
Rumus, rujukan silang, angka, dan kutipan lain sudah diperiksa identik (hanya empat \cite baru yang sengaja ditambah). Idempoten. Akhir baris dipertahankan. Cadangan: .pre-prose3.bak.
   python scripts/apply_prose_edits_3.py [--tex manuscript/sn-article.tex] [--dry-run]"""
import argparse, shutil, sys
from pathlib import Path
EDITS = [
  ('K1', 'Methods 3.3 (kutipan)',
   'consisted of Prometheus, Prometheus Operator',
   'consisted of Prometheus~\\cite{prometheus_overview}, Prometheus Operator'),
  ('K2', 'Methods 3.4 (kutipan)',
   '10{,}000-resample bootstrap confidence interval (fixed seed)',
   '10{,}000-resample bootstrap~\\cite{efron1979bootstrap} confidence interval (fixed seed)'),
  ('K3', 'Methods 3.9 (kutipan)',
   'its own Holm correction at $\\alpha=0.025$',
   'its own Holm correction~\\cite{holm1979simple} at $\\alpha=0.025$'),
  ('K4', 'Methods 3.5 (kutipan)',
   'one CISA KEV catalogue download',
   'one CISA KEV catalogue~\\cite{cisa_kev} download'),
  ('M1', 'Methods 3.5',
   'At the time of writing the inventory holds 120 assets (117 images across web, proxy, cache, database,\nqueue, runtime, base, observability, and Kubernetes-native infrastructure and security tooling categories, plus\nP0 and the two P0-IF conditions) across the 57-week window: 6{,}833 asset-week rows, after excluding seven rows whose evidence remained unresolved\n(one CockroachDB CVE under Trivy status \\texttt{under\\_investigation} at the inventory freeze date) a\nnon-missing rate of 0.93 and zero rows left in an unresolved evidence state.',
   'At the time of writing the inventory holds 120 assets (117 images across web, proxy, cache, database, queue, runtime, base, observability, and Kubernetes-native infrastructure and security tooling categories, plus P0 and the two P0-IF conditions) observed across the 57-week window. It comprises 6{,}833 asset-week rows, after excluding seven rows whose evidence remained unresolved (one CockroachDB CVE under Trivy status \\texttt{under\\_investigation} at the inventory freeze date); the non-missing rate is 0.93, and no row is left in an unresolved evidence state.'),
  ('M3', 'Methods 3.5',
   "The three open decisions on label\naggregation, label scale, and the definition of Patch Risk were closed by cross-checking the\ndecomposition above against this subsection's own formula rather than treated as free parameters: the\nrow-wise maximum and the raw 0--100 scale are the definition as written, not a choice, and the\n\\{0,1,2\\} Patch Risk contract already matches the running pipeline.",
   "The three open decisions on label aggregation, label scale, and the definition of Patch Risk were closed by cross-checking the decomposition above against this subsection's own formula; they were not treated as free parameters. The row-wise maximum and the raw 0--100 scale are the definition as written, not a choice, and the \\{0,1,2\\} Patch Risk contract already matches the running pipeline."),
  ('M4a', 'Methods 3.5',
   'Each image contributes one frozen, digest-pinned Trivy~\\cite{aqua_trivy} vulnerability scan; CVEs lacking a\npublication date (a known Debian/Ubuntu-tracker gap) are dated by the first sealed weekly snapshot in\nwhich they are scored, and a CVE that never appears in any sealed snapshot is excluded from the active\nset rather than assumed absent.',
   'Each image contributes one frozen, digest-pinned Trivy~\\cite{aqua_trivy} vulnerability scan. CVEs lacking a publication date (a known Debian/Ubuntu-tracker gap) are dated by the first sealed weekly snapshot in which they are scored, and a CVE that never appears in any sealed snapshot is excluded from the active set rather than assumed absent.'),
  ('M4b', 'Methods 3.5',
   'A positive control, P0-IF, isolates one asset with the image-filter\nNginx module either inactive ($\\rho=0.25$: transitively present, unloaded) or active with its trigger\npath exercised ($\\rho=1$), built from the same digest-pinned base image as the primary asset P0 so that\nits vulnerability surface (109 of 135 known CVEs as of the freeze date, 25 in \\texttt{libexpat}) is not\nan artefact of an unrelated rebuild.',
   'A positive control, P0-IF, isolates one asset with the image-filter Nginx module either inactive ($\\rho=0.25$: transitively present, unloaded) or active with its trigger path exercised ($\\rho=1$). It is built from the same digest-pinned base image as the primary asset P0, so its vulnerability surface (109 of 135 known CVEs as of the freeze date, 25 in \\texttt{libexpat}) is not an artefact of an unrelated rebuild.'),
  ('M5', 'Methods 3.7',
   "The two nodes together used on average about 230~mCPU without and 329~mCPU with the monitoring stack, i.e.\\ 1.4\\% and 2.1\\% of the host's 16 logical cores (capacity from the v4.2 collector metadata and \\texttt{docker info}; it was not logged during Runs~7--16), so the absence of a latency effect was observed at low utilisation and need not extend to saturated nodes.",
   "The two nodes together used on average about 230~mCPU without and 329~mCPU with the monitoring stack, i.e.\\ 1.4\\% and 2.1\\% of the host's 16 logical cores (capacity from the v4.2 collector metadata and \\texttt{docker info}; it was not logged during Runs~7--16). The absence of a latency effect was therefore observed at low utilisation and need not extend to saturated nodes."),
  ('T1', 'Results 4.4',
   'reproduction directly rather than merely asserting it:',
   'reproduction directly:'),
  ('T2', 'Results 4.5',
   'confirming the hybrid scheme as necessary rather than incidental.',
   'confirming that the hybrid scheme is necessary.'),

]
ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--tex", default="manuscript/sn-article.tex"); ap.add_argument("--dry-run", action="store_true"); a = ap.parse_args()
p = Path(a.tex)
if not p.exists(): sys.exit(f"ABORT: {p} tidak ada")
text = open(p, encoding="utf-8", newline="").read(); crlf = "\r\n" in text
if crlf: text = text.replace("\r\n", "\n")
applied, already, skipped, multi = [], [], [], []
for i, sec, old, new in EDITS:
    n_old, n_new = text.count(old), text.count(new)
    done = (n_new >= 1) if old in new else (n_old == 0 and n_new >= 1)
    if done: already.append(i); continue
    if n_old > 1: multi.append(i); continue
    if n_old == 1: text = text.replace(old, new, 1); applied.append(i)
    else: skipped.append(i)
if multi: sys.exit("ABORT, tidak ada yang ditulis: teks lama muncul lebih dari sekali untuk " + ", ".join(multi))
print(f"Diterapkan ({len(applied)}): {', '.join(applied) or '-'}")
print(f"Sudah ada sebelumnya ({len(already)}): {', '.join(already) or '-'}")
print(f"DILEWATI, teks lama tidak cocok ({len(skipped)}): {', '.join(skipped) or '-'}")
if a.dry_run or not applied: print("(dry-run atau tidak ada perubahan; tidak ada yang ditulis)"); sys.exit(0)
out = text.replace("\n", "\r\n") if crlf else text
shutil.copy(p, str(p) + ".pre-prose3.bak"); open(p, "w", encoding="utf-8", newline="").write(out)
print("OK: berkas ditulis" + ("; sebagian dilewati: kirim keluaran ini agar saya sesuaikan dengan berkas terbaru" if skipped else ""))
