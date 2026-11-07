#!/usr/bin/env python3
"""apply_claims_consistency.py - perbaikan konsistensi dan penyempitan klaim naskah berdasarkan audit 7 November 2026 (berkas 08 dan 10) dan hasil E25, E26, E27.

Lapisan (P1): naskah (pelaporan klaim). Dokumen: manuscript/sn-article.tex. Dasar: protokol beku E4 menamai perbandingan terhadap FlatANFISMatched 'H2/H3'; H4 tidak pernah diuji; C2 dan H2 menjanjikan pengukuran komputasi (kini E25: waktu latih dan latensi tidak terdukung);
label menggunakan hanya EPSS, KEV, dan reachability; paritas 981 baris berasal dari inventaris 109 aset; pusat MF variabel antara tidak berurutan (E27). Kalimat skenario A templat E7 tidak diubah; kualifikasi ditambahkan sesudahnya.
Kata definisi hipotesis H1a sampai H5 tidak berubah. Tidak ada angka hasil yang diubah; angka baru hanya yang berasal dari E25 sampai E27.
Teks-persis, gagal-tertutup: tiap teks lama harus cocok TEPAT SATU KALI (spasi dan baris baru dinormalkan) sebelum apa pun ditulis.
Idempoten: bila semua teks baru sudah terpasang, keluar 0 tanpa menulis. Keadaan campuran = ABORT.
Akhir baris (LF/CRLF) dipertahankan. Cadangan: manuscript/sn-article.tex.pre-claims.bak.
Jalankan dari root repo:  python3 Patch/apply_claims_consistency.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex")
if not (os.path.isfile(P) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo (harus ada .git dan manuscript/sn-article.tex)")

PAIRS = [('\\abstract{Static, expert-weighted fuzzy risk scores go stale between elicitations, while a flat Adaptive Neuro-Fuzzy Inference System (ANFIS) '
  'over seven risk inputs requires 128 rules and 1{,}052 parameters. We propose a hierarchical ANFIS (HANFIS) that separates vulnerability and '
  'environmental reasoning before an integration tier adds threat intelligence, reducing the model to 34 rules and 176 parameters (73.4\\% and '
  '83.3\\% fewer). We build a temporal exploitability-exposure target from sealed weekly Exploit Prediction Scoring System (EPSS) and Known '
  'Exploited Vulnerabilities (KEV) snapshots for 120 container images (6{,}357 asset-weeks), evaluated with grouped, embargoed splits. A 4-week '
  'persistence baseline lowers mean squared error relative to climatology by 97\\%; a single Common Vulnerability Scoring System (CVSS) score, by '
  '22\\%. Under a protocol frozen before training, HANFIS reduces mean squared error by 96.7\\% against CVSS, 69.6\\% against a linear model and '
  '66.5\\% against a parameter-matched flat ANFIS (95\\% bootstrap intervals excluding zero), but is not distinguishable from persistence. Post hoc '
  'analyses qualify these gains. Exact Shapley attribution puts 78.9\\% on exploitability and the KEV indicator, ingredients of the label, and '
  'without them HANFIS has no skill over CVSS (skill $-0.14$, interval $-0.34$ to $0.05$). A four-parameter formula of those two inputs, '
  '$100\\max(x_2,0.1\\,x_7)$, has a lower error than HANFIS at four weeks (skill $-0.53$, interval $-1.44$ to $-0.21$); the gap narrows at longer '
  'horizons only through weeks around an EPSS model change. In a pre-registered forward evaluation, the formula beat persistence and HANFIS did not '
  'beat the formula. The data cannot show whether environmental context helps.}',
  '\\abstract{Static, expert-weighted fuzzy risk scores go stale between elicitations, while a flat Adaptive Neuro-Fuzzy Inference System (ANFIS) '
  'over seven risk inputs requires 128 rules and 1{,}052 parameters. We propose a hierarchical ANFIS (HANFIS) that separates vulnerability and '
  'environmental reasoning before an integration tier adds threat intelligence, reducing the model to 34 rules and 176 parameters (73.4\\% and '
  '83.3\\% fewer). We build a temporal exploitability-exposure target from sealed weekly Exploit Prediction Scoring System (EPSS) and Known '
  'Exploited Vulnerabilities (KEV) snapshots for 120 container images (6{,}357 labelled asset-weeks), evaluated with grouped, embargoed splits. A '
  '4-week persistence baseline lowers mean squared error relative to climatology by 97\\%; a single Common Vulnerability Scoring System (CVSS) '
  'score, by 22\\%. Under a protocol frozen before training, HANFIS reduces mean squared error by 96.7\\% against CVSS, 69.6\\% against a ridge '
  'model on all seven inputs and 66.5\\% against a parameter-matched flat ANFIS (95\\% bootstrap intervals excluding zero; the last margin comes '
  'largely from one fold), but is not distinguishable from persistence. Post hoc analyses qualify these gains. Exact Shapley attribution puts '
  '78.9\\% on exploitability and the KEV indicator, ingredients of the label, and without them HANFIS has no skill over CVSS (skill $-0.14$, '
  'interval $-0.34$ to $0.05$). A four-parameter formula of those two inputs, $100\\max(x_2,0.1\\,x_7)$, has a lower error than HANFIS at four weeks '
  '(skill $-0.53$, interval $-1.44$ to $-0.21$). In a pre-registered forward evaluation, the formula beat persistence and HANFIS did not beat the '
  'formula. The data cannot show whether environmental context helps.}'),
 ('Nonlinear Risk Mitigation, Security Risk Assessment', 'Exploit prediction, Security Risk Assessment'),
 ('ANFIS is a hybrid algorithm that integrates the learning ability of ANN into the FIS design procedure.',
  'ANFIS is a hybrid algorithm that integrates the learning ability of ANN into the FIS design procedure~\\cite{jang1993anfis}.'),
 ('following the requirement that reduced intermediate variables remain semantically interpretable (Lee, Chung, and Yu~\\cite{lee2003hierarchical}).',
  'following the requirement that reduced intermediate variables remain semantically interpretable (Lee, Chung, and Yu~\\cite{lee2003hierarchical}); '
  'Section~\\ref{subsec:e27} shows that the trained centres of $v$ and $e$ do not always keep that order.'),
 ('A domain-informed HANFIS architecture that separates vulnerability and environmental reasoning before integrating their outputs with dynamic '
  'threat intelligence to produce a continuously recalculated Dynamic Risk Score.',
  'A domain-informed HANFIS architecture, proposed as a design, that separates vulnerability and environmental reasoning before integrating their '
  'outputs with threat intelligence to produce a Dynamic Risk Score recalculated weekly from sealed EPSS and KEV snapshots. Unlike the '
  'speaker-verification HANFIS of~\\cite{soozanchi2010hanfis}, its three tiers follow a vulnerability, environment and threat decomposition, and the '
  'evaluation does not show that the environmental panel contributes (Sections~\\ref{subsec:e8} and~\\ref{subsec:e9}).'),
 ('A computational optimization strategy that changes exhaustive rule growth from $m^{7}$ to $2m^{3}+m_I^{2}m$, accompanied by empirical '
  'measurements of parameter count, training cost, memory consumption, throughput, and inference latency.',
  'A hierarchical decomposition that changes exhaustive rule growth from $m^{7}$ to $2m^{3}+m_I^{2}m$ (the arithmetic of hierarchical fuzzy '
  'systems~\\cite{raju1991,wang1998hierarchical}), accompanied by an unregistered measurement of parameter count, training time, peak memory, '
  'throughput and single-row inference latency against flat ANFIS variants (Section~\\ref{subsec:e25}). It lowers parameters and peak training '
  'memory and raises batch throughput relative to the full flat model, but not training time or single-row latency.'),
 ('An operational definition of dynamic cybersecurity risk that combines CVSS Base severity, patch condition, MFA weakness, Kubernetes exposure, '
  'asset criticality, and time-varying threat evidence without duplicating CVSS threat metrics.',
  'An operational definition of seven risk inputs (CVSS Base severity, exploitability, patch condition, MFA weakness, Kubernetes exposure, asset '
  'criticality, and time-varying threat evidence, without duplicating CVSS threat metrics) and of a realised 30-day exploitability-exposure target '
  'built from sealed EPSS and KEV snapshots. The target has no impact term, so it measures exploitability exposure, not full cybersecurity risk.'),
 ('results are reported in Section~\\ref{subssec4.3} (Table~\\ref{tab:e4-results}).',
  'results are reported in Section~\\ref{subssec4.3} (Table~\\ref{tab:e4-results}). In the frozen protocol, H2 and H3 are tested together by one '
  'comparison, the skill score against FlatANFISMatched with a non-inferiority margin of $-0.05$ on the lower confidence bound; it is labelled H2/H3 '
  'below. The computational part of H2 (training time, memory, latency) was not part of that protocol and is reported separately as an unregistered '
  'measurement (Section~\\ref{subsec:e25}).\n'
  '\n'
  '\\textbf{H4 (threat responsiveness)} was not tested as stated: the registered protocols contain no test of it, and the closest procedure, an '
  'ablation of $x_7$ alone run afterwards, is reported as a post hoc, unregistered analysis (Section~\\ref{subsec:e26}).\n'
  '\n'
  'The remainder of the paper is organised as follows. Section~\\ref{sec2} reviews ANFIS and hierarchical fuzzy systems. Section~\\ref{sec3} '
  'describes the architecture, the testbed, the realised exploitability-exposure target and the pre-registered forward evaluation. '
  'Section~\\ref{sec4} reports the observability-overhead measurements, the confirmatory comparison, the ablations and post hoc analyses, the '
  'computational-cost measurement, and the forward evaluation. Section~\\ref{sec5} discusses the findings and their limits, and Section~\\ref{sec6} '
  'concludes.'),
 ('Its computational cost is measured (rule count, trainable parameters, training duration, peak memory, throughput, and median and tail inference '
  'latency), and edge-platform measurements are left to future work.',
  'Its computational cost is compared with flat ANFIS variants on one machine (rule count, trainable parameters, training time, peak memory, '
  'throughput, and single-row inference latency; Section~\\ref{subsec:e25}), and edge-platform measurements are left to future work.'),
 ('(H1a--H1c, H2, H3) are pre-registered under a frozen',
  '(H1a--H1c and H2/H3, which the frozen protocol tests together) are pre-registered under a frozen'),
 ('HANFIS confirms H1a, H1c, and H2, does not confirm H1b', 'HANFIS confirms H1a, H1c, and H2/H3, does not confirm H1b'),
 ('H2 & FlatANFISMatched & 0.665', 'H2/H3 & FlatANFISMatched & 0.665'),
 ("H2's margin is large for two models", 'The H2/H3 margin is large for two models'),
 ('H1a, H1c and H2 remain confirmed', 'H1a, H1c and H2/H3 remain confirmed'),
 ('Two further observations qualify H2.', 'Two further observations qualify H2/H3.'),
 ("H2's pooled margin is dominated by the first fold", 'The H2/H3 pooled margin is dominated by the first fold'),
 ('a parameter-matched flat ANFIS initialised by subtractive clustering (H2).',
  'a parameter-matched flat ANFIS initialised by subtractive clustering (H2/H3).'),
 ("H1b's confidence interval crosses zero, so HANFIS is not distinguishable",
  "The H1a comparator, a single CVSS score, has no access to exploitability or the KEV indicator, the two inputs that carry HANFIS's skill "
  '(Section~\\ref{subsec:e9}), and the H1c comparator, a ridge model on all seven inputs, is itself worse than persistence '
  '(Table~\\ref{tab:e3-baselines}).\n'
  '\n'
  "H1b's confidence interval crosses zero, so HANFIS is not distinguishable"),
 ("(Section~\\ref{subssec4.3}'s baseline table above)", '(Table~\\ref{tab:e3-baselines})'),
 ('A per-row comparison against the $k{=}1$ predictions underlying Table~\\ref{tab:e4-results} confirms this reproduction directly: Pearson '
  '$r=0.9984$ on point predictions, and identical fold assignment for all 981 held-out rows.',
  'A per-row comparison with the confirmatory predictions on the earlier 109-asset inventory confirmed this reproduction directly (Pearson '
  '$r=0.9984$ on point predictions, identical fold assignment for all 981 held-out rows); the comparison was not repeated on the 120-asset '
  'inventory.'),
 ('(P7a supported)', '(P7a supported: HANFIS not better)'),
 ('[$-$9.177, $-$1.594] & Supported \\\\', '[$-$9.177, $-$1.594] & Supported (HANFIS not better) \\\\'),
 ('[$-$13.677, $-$3.188] & Supported \\\\', '[$-$13.677, $-$3.188] & Supported (HANFIS not better) \\\\'),
 ('\\section{Discussion}\\label{sec5}\n\nThree findings',
  '\\section{Discussion}\\label{sec5}\n'
  '\n'
  'For a practitioner who needs to rank vulnerabilities by near-term exploitability exposure today, the evidence supports a simple choice: the '
  'max-form formula of the EPSS and KEV signals, with persistence as the comparator that any alternative must beat. HANFIS remains relevant only '
  'where an auditable rule structure is required and where an outcome that depends on the environment is available to test the environmental panel.\n'
  '\n'
  'Three findings'),
 ('We did not test why the trained model transferred worse than the formula.',
  'We did not test why the trained model transferred worse than the formula. Its rule base can be printed (Tables~S11 to S13 of Additional file~1), '
  'but the linguistic labels of its intermediate variables cannot be read from the membership index in most trained models '
  '(Section~\\ref{subsec:e27}), so the readability of the rule base is a property of its structure, not of its terms.'),
 ('they are descriptive, carry no multiplicity correction, and none of them changes a registered decision.',
  'they are descriptive, carry no multiplicity correction, and none of them changes a registered decision. The cost measurement (E25), the $x_7$ '
  'ablation (E26) and the rule documentation (E27) were run after the forward evaluation, use no forward data, and are unregistered.'),
 ('not better accuracy than a simple formula at the four-week horizon.',
  'not better accuracy than a simple formula at the four-week horizon. Its intermediate variables do not keep a stable linguistic meaning across '
  'trained models (Section~\\ref{subsec:e27}).'),
 ('not as evidence for one (Section~\\ref{subssec4.5}).',
  'not as evidence for one (Section~\\ref{subssec4.5}). Against the flat ANFIS variants, HANFIS lowers parameters and peak training memory but not '
  'training time or single-row latency (Section~\\ref{subsec:e25}).'),
 ('Two further contributions are established: the sealed, hash-verified real-world data pipeline (120 assets and 6{,}357 labelled asset-weeks, '
  'Section~\\ref{subsec:target-definition}) and a completed ablation showing that the monotonicity constraint has a membership-family-dependent '
  'accuracy cost, met in practice only for the dominant drivers (Sections~\\ref{subssec4.5} and~\\ref{subsec:e8}).',
  'Two further results are documented: the sealed, hash-verified real-world data pipeline (120 assets and 6{,}357 labelled asset-weeks, '
  'Section~\\ref{subsec:target-definition}) and an ablation on two synthetic scenarios indicating that the monotonicity constraint has a '
  'membership-family-dependent accuracy cost, met in practice only for the dominant drivers (Sections~\\ref{subssec4.5} and~\\ref{subsec:e8}).')]


def rx(text):
    return re.compile(r"\s+".join(re.escape(t) for t in text.split()))


raw = open(P, "rb").read()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")

state = []
for n, (old, new) in enumerate(PAIRS, 1):
    co, cn = len(rx(old).findall(s)), len(rx(new).findall(s))
    nrm = lambda z: " ".join(z.split())
    if co == 1 and cn == 0:
        state.append("old")
    elif cn >= 1 and (co == 0 or nrm(old) in nrm(new)):
        state.append("new")
    else:
        sys.exit(f"ABORT: pasangan {n}: teks lama cocok {co} kali, teks baru {cn} kali; tidak ada yang ditulis")
if all(x == "new" for x in state):
    print("SUDAH TERPASANG: semua", len(PAIRS), "suntingan; tidak ada yang ditulis")
    sys.exit(0)
if any(x == "new" for x in state):
    sys.exit("ABORT: keadaan campuran (sebagian suntingan sudah terpasang); tidak ada yang ditulis")

for n, (old, new) in enumerate(PAIRS, 1):
    s, k = rx(old).subn(lambda m, new=new: new, s, count=1)
    if k != 1:
        sys.exit(f"ABORT: pasangan {n} tidak dapat diterapkan; tidak ada yang ditulis")

out = (s.replace("\n", "\r\n") if crlf else s).encode("utf-8")
with open(P + ".pre-claims.bak", "wb") as f:
    f.write(raw)
with open(P, "wb") as f:
    f.write(out)
print("OK", len(PAIRS), "suntingan |", "CRLF" if crlf else "LF", "| cadangan", P + ".pre-claims.bak")
