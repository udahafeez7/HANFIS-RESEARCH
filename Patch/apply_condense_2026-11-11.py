#!/usr/bin/env python3
r"""apply_condense_2026-11-11.py - pemadatan naskah C.1 sampai C.7 (penilaian 11 November 2026).

Lapisan (P1): naskah (pelaporan). Dokumen: manuscript/sn-article.tex, manuscript/additional_file_1.tex.
Blok yang dipindah utuh ke Additional file 1 (teks asli, tabel dan gambar ikut): protokol overhead observabilitas dan pengaman validitas
(Note S8, Table S14), horizon sweep (Note S9, Table S15), anatomi galat (Note S10, Table S16), kurva akurasi-kompleksitas (Note S11,
Figure S5). Teks utama diganti ringkasan dengan angka kunci yang sama. E6, E15, E21 dipadatkan (tabel dan catatan S3, S4, S6 sudah ada).
Judul subbagian tanpa kode E; sebutan 'amendment A-xx' dihapus dari badan dan dipetakan di Table S17. Tidak ada angka hasil yang diubah;
angka yang keluar dari badan tetap ada di Additional file 1.
Gagal-tertutup: setiap jangkar harus cocok tepat satu kali (spasi dinormalkan) di kedua berkas sebelum apa pun ditulis. Idempoten.
CRLF dipertahankan. Cadangan .pre-condense.bak. Jalankan dari root repo:  python3 Patch/apply_condense_2026-11-11.py
"""
import os, re, sys

P = os.path.join("manuscript", "sn-article.tex"); A = os.path.join("manuscript", "additional_file_1.tex")
if not (os.path.isfile(P) and os.path.isfile(A) and os.path.isdir(".git")):
    sys.exit("ABORT: jalankan dari root repo")
DONE_MARK = "\\section*{Supplementary material moved from the main text on 11 November 2026}"


def rx(text):
    return re.compile(r"\s+".join(re.escape(t) for t in text.split()))


def find1(s, text, what):
    ms = list(rx(text).finditer(s))
    if len(ms) != 1:
        sys.exit(f"ABORT: jangkar '{what}' cocok {len(ms)} kali; tidak ada yang ditulis")
    return ms[0]


def cut(s, start, end, what):
    a = find1(s, start, what + " (awal)"); b = find1(s, end, what + " (akhir)")
    if b.start() <= a.start():
        sys.exit(f"ABORT: urutan jangkar '{what}' terbalik")
    return s[:a.start()], s[a.start():b.start()], s[b.start():]


def strip_env(block, env, label):
    pat = re.compile(r"\\begin\{" + env + r"\}.*?\\end\{" + env + r"\}\s*", re.S)
    out, n = [], 0
    pos = 0
    for m in pat.finditer(block):
        if label in m.group(0):
            out.append(block[pos:m.start()]); pos = m.end(); n += 1
    out.append(block[pos:])
    if n != 1:
        sys.exit(f"ABORT: lingkungan {env} dengan label {label} cocok {n} kali")
    return "".join(out)


def take_env(block, env, label):
    for m in re.finditer(r"\\begin\{" + env + r"\}.*?\\end\{" + env + r"\}", block, re.S):
        if label in m.group(0):
            return m.group(0)
    sys.exit(f"ABORT: lingkungan {env} dengan label {label} tidak ditemukan")


# ---------- teks utama baru ----------
PLATFORM_NEW = r"""\subsection{Experimental platform and telemetry validation}
\label{subsec3.2}\label{subsec:overhead-protocol}
The experimental workflow ran in Ubuntu 24.04 under Windows Subsystem for Linux 2 (WSL~2), with Docker Desktop as container runtime and Kubernetes integration. The testbed had two Ready nodes and a baseline application, P0, deployed with two ready replicas in the \texttt{hanfis-research} namespace; a load-generator pod reached P0 through an internal service, and status code 200 was required at every gate. The observability stack (Prometheus~\cite{prometheus_overview}, Prometheus Operator, kube-state-metrics and node-exporter) ran in a separate \texttt{monitoring} namespace and was scaled to zero in the OFF condition, with the original definitions saved so that the ON state could be restored. Preparation followed a sequence of auditable gates with SHA-256 manifests (Table~S1 of Additional file~1); the evidence that the gates were met is the set of archives for Runs~7--16.

The observability-overhead protocol, \texttt{external-v3.0}, has ten counterbalanced ON--OFF run pairs (Runs~7--16), a fail-closed admission rule under which a failed gate yields a \texttt{HOLD} decision and no observation, the run as the independent replication unit, an exact two-sided sign-flip test over the ten paired differences (smallest attainable $p$ of $2/2^{10}=0.002$) and a 10{,}000-resample bootstrap~\cite{efron1979bootstrap} interval for the mean difference. Its full description, the overhead definitions and the validity safeguards are in Supplementary note S8 of Additional file~1. The estimated increment is an instrumentation cost and is not read as a change in application exposure; runtime telemetry is not an input of the model (Section~\ref{subsec:hanfis-integration}).

"""

OVERHEAD_NEW = r"""\subsection{Observability overhead}
\label{subsec4.1}

Ten counterbalanced run pairs passed every gate (Runs 7--16); one aborted attempt each of Run~7 and Run~17 failed the integrity gate and were recorded as incidents. Table~S14 of Additional file~1 gives the paired differences. The resource cost of the stack is large and has the same direction in every pair: node CPU $+99.36$~mCPU (95\% CI $[96.29,\ 103.35]$, $+43.3\%$) and node memory $+280.76$~MiB ($[250.99,\ 303.54]$, $+18.7\%$), of which the monitoring namespace itself accounts for only $39.79$~mCPU and $204.19$~MiB, so pod-level accounting understates the platform cost by a factor of about $2.5$ (effect size $d_z = 16.5$ for node CPU); the remainder is induced platform work (kubelet, cAdvisor, container runtime and the API server). The cost does not reach the observed workload: median and P95 latency change by $-0.005$~ms ($[-0.055,\ +0.044]$) and $+0.059$~ms ($[-0.126,\ +0.265]$), below $3\%$ of the baseline, and the P0 container uses $0.334$~MiB less memory under monitoring ($p = 0.016$), an effect of no practical size. The intervals bound the latency effect without establishing equivalence.

"""

ACC_NEW = r"""\subsection{Accuracy-complexity curve}
\label{subssec4.4}

The scalar bottleneck between the lower panels and the integration panel is a candidate explanation for any residual gap between HANFIS and a full-capacity flat ANFIS, because compressing $v$ and $e$ to one number each may discard cross-subsystem interaction. A sweep over the bottleneck width $k$ passes $k$-dimensional $v$ and $e$ into the integration panel. Under grid partitioning the integration rule count grows as $m_I^{2k}\cdot m$: at the frozen $m_I=3$, $k=1$ is HANFIS itself (34 rules, 176 parameters), $k=2$ costs 178 rules and 1{,}152 parameters, and $k\ge3$ exceeds 1{,}400 rules, more parameters than the inventory has rows (Figure~\ref{fig:e5-rule-growth}). The sweep script refuses such settings, so we ran $k\in\{1,2\}$. At $k{=}1$ the sweep reproduces the frozen training scheme; a per-row comparison on the earlier 109-asset inventory gave Pearson $r=0.9984$ against the confirmatory predictions over 981 held-out rows. Supplementary note S11 of Additional file~1 holds the full account, including an earlier, confounded version of the sweep that the numbers here supersede.

__FIG_RULE_GROWTH__

__TAB_E5__

$k{=}1$ recovers skill consistent with the H1b result (Table~\ref{tab:e4-results}: $\mathrm{SS}_{\mathrm{pers}}=0.015$, $[-0.607,0.246]$); both intervals cross zero. $k{=}2$ is worse than persistence, with an interval entirely below zero. The paired difference on matched resamples, $\mathrm{SS}_{\mathrm{pers}}(k{=}1)-\mathrm{SS}_{\mathrm{pers}}(k{=}2)=0.791$ (95\% CI $[0.354,2.037]$), excludes zero, and $k{=}1$ has the lower pooled RMSE on all five folds (two-sided sign test $p=0.0625$, the floor with five folds; Figure~S5 of Additional file~1). This is a mechanism claim rather than proof that wider bottlenecks are intrinsically worse: every $k{=}2$ fold falls below ten observations per parameter (range 0.3--2.9), while $k{=}1$ clears that threshold in three of five folds. Disabling the hard clamp on $v,e$ costs $k{=}1$ 0.161 of skill and $k{=}2$ 0.813, consistent with $v,e$ being estimated less reliably once six times as many consequent parameters compete for the same rows. Separating an intrinsic cost of wider bottlenecks from this data-scale effect needs an inventory far larger than 120 assets.

"""

E6_NEW = r"""\subsection{Explanation fidelity}\label{sec:e6}
We tested whether the rule-level explanation that HANFIS exposes is faithful to its inference, using the 25 saved models (five folds $\times$ five seeds), which reproduce the confirmatory predictions exactly. The run is reported as a documented deviation, because the version-control freeze preceded the commit that contained the protocol text. The rule-attribution check failed its criterion: removing the three rules ranked highest by attribution changed the output 4.1 times more than removing three random rules, but exceeded the median random removal in only 83.5\% of non-degenerate rows (criterion: 90\%); 552 of the 575 positive-control pairs increased strictly. We therefore do not claim validated rule-level explanations. The rule trace matches the inference and the direction of the response is verified, but the attribution of the output to individual rules is faithful on average and not uniformly (Table~S4 and Supplementary note S3 of Additional file~1).

"""

E14_NEW = r"""\subsection{Horizon sweep}\label{subsec:e14}
To check whether the conclusions depend on the four-week label window, we rebuilt the labels with windows of 58 and 86 days (eight and twelve weekly snapshots), set the persistence lag and the embargo to the window length, and repeated the out-of-fold comparison with the same folds, seeds and hyperparameters (post hoc; 889 and 697 rows; only skill scores are comparable across horizons). The formula keeps its advantage over persistence (skill $0.36$, $0.49$ and $0.44$ at four, eight and twelve weeks). The gap between HANFIS and the formula closes with the horizon: $-0.534$ (interval $[-1.438,\,-0.208]$), $-0.048$ ($[-0.205,\,0.032]$) and $0.039$ ($[-0.031,\,0.110]$). Longer windows contain only older weeks, so horizon and period are confounded; on the 408 asset-weeks present at all three horizons the change in the skill of HANFIS against the formula is $+0.862$ ($[+0.309,\,+2.973]$), while the skill of the formula against persistence does not change. Without exploitability and the KEV indicator HANFIS has no skill over CVSS at any horizon ($-0.099$ and $-0.179$ at eight and twelve weeks). Section~\ref{subsec:e16} shows that the narrowing comes largely from weeks around the EPSS model change. The full results are in Table~S15 and Supplementary note S9 of Additional file~1.

"""

E15_NEW = r"""\subsection{Prioritisation utility}\label{subsec:e15}
Because risk scores are used to rank assets, we also compared the predictors on weekly ranking (post hoc; out-of-fold predictions at three horizons; weekly Spearman correlation and precision at the top 20\%; Tables~S5 and~S6 and Supplementary note S4 of Additional file~1). All predictors rank assets almost identically. At four weeks the weekly Spearman correlation is $0.99$ for the formula and for persistence and $0.97$ for HANFIS, and the precision at the top 20\% is $0.97$ for all three, so the lower squared error of the formula brings no practical gain in prioritisation. With eighteen paired comparisons and no correction for multiplicity, the intervals are descriptive.

"""

E16_NEW = r"""\subsection{Error anatomy and the EPSS model change}\label{subsec:e16}
To see where the pooled differences come from, we analysed the four-week out-of-fold predictions by input-change stratum and by distance to the change of the EPSS model on 2026-06-15 (post hoc; bootstrap clustered by image; Tables~S7 and~S16 and Supplementary note S10 of Additional file~1). The advantage of the formula over persistence sits in the 628 of 1{,}080 rows in which an input changed during the previous four weeks (skill $0.400$, interval $0.308$ to $0.487$) and vanishes where nothing changed ($0.002$). HANFIS has skill $0.125$ in changed rows and $-0.900$ ($-4.171$ to $-0.206$) in unchanged rows: it adds noise where persistence already suffices. The largest errors fall in the weeks 2026-W21 to W24, whose label windows straddle the model change; these 190 rows hold 77\% of the squared error of persistence and of the formula and 49\% of that of HANFIS. On the remaining 890 rows the formula keeps its point estimate against persistence ($0.348$ against $0.357$, interval now $-0.060$ to $0.422$), whereas HANFIS is worse than persistence ($-1.228$) and than the formula ($-2.418$). On unaffected rows at eight and twelve weeks HANFIS stays behind the formula ($-0.324$ and $-0.362$, intervals including zero), so the deficit shrinks with the horizon without closing. The forward evaluation (Section~\ref{subsec:e7-results}) is free of this change.

"""

E21_NEW = r"""\subsection{Calibration}\label{subsec:e21}
Calibration was checked after the registration of the forward evaluation had become public (post hoc, descriptive, no training; Table~S8 and Supplementary note S6 of Additional file~1). All three predictors lie close to the identity line. Persistence runs low on all rows (mean error $-0.097$, interval $-0.196$ to $-0.013$), almost entirely because of the weeks around the EPSS model change (on unaffected rows $-0.015$, $-0.079$ to $0.025$). HANFIS departs most, with slope $1.025$ ($1.008$ to $1.044$) on all rows and, on unaffected rows, slope $1.031$ ($1.014$ to $1.053$) and intercept $-0.193$ ($-0.300$ to $-0.085$); these departures are small next to the label scale. A cross-fitted linear recalibration does not close the gap to the formula (skill of HANFIS against the formula $-0.534$, $-1.383$ to $-0.204$, before and $-0.535$, $-1.287$ to $-0.232$, after), and stacking finds no information in HANFIS that a straight line can use (skill of the combination against the recalibrated formula $-0.001$, $-0.006$ to $0.004$).

"""

HEADINGS = [
 (r"\subsection{HANFIS architecture, rule count, and parameter complexity}", r"\subsection{Rule count and parameter budget}"),
 (r"\subsection{Attribution and monotonicity checks (E8)}\label{subsec:e8}", r"\subsection{Attribution and monotonicity checks}\label{subsec:e8}"),
 (r"\subsection{Label-ingredient ablation and information-minimal baselines (E9--E11)}", r"\subsection{Label-ingredient ablation and information-minimal baselines}"),
 (r"\subsection{Threat-intelligence ablation (E26)}\label{subsec:e26}", r"\subsection{Threat-intelligence ablation}\label{subsec:e26}"),
 (r"\subsection{Trained rules and membership order (E27)}\label{subsec:e27}", r"\subsection{Trained rules and membership order}\label{subsec:e27}"),
 (r"\subsection{Computational cost against flat ANFIS variants (E25)}\label{subsec:e25}", r"\subsection{Computational cost against flat ANFIS variants}\label{subsec:e25}"),
 (r"\subsection{Prospective evaluation (E7): pre-registered design}\label{subsec:e7}", r"\subsection{Forward evaluation: pre-registered design}\label{subsec:e7}"),
 (r"\subsection{Prospective evaluation (E7): forward results}\label{subsec:e7-results}", r"\subsection{Forward evaluation: results}\label{subsec:e7-results}"),
]
AMEND = [
 (r"With the frozen configuration $m=2$, $m_I=3$ (amendment A-02), the proposed structure", r"With the frozen configuration $m=2$, $m_I=3$, the proposed structure"),
 (r"inside the integration panel use $m_I=3$ (amendment A-02), which turns", r"inside the integration panel use $m_I=3$, which turns"),
 (r"through a softplus reparameterisation (amendment A-04), so that", r"through a softplus reparameterisation, so that"),
 (r"Training is hybrid (amendment A-06): the", r"Training is hybrid: the"),
 (r"All results below use the frozen configuration of amendment A-09: hybrid closed-form/Adam training",
  r"All results below use the frozen configuration (the protocol amendments that fixed each setting are listed in Table~S17 of Additional file~1): hybrid closed-form/Adam training"),
 (r"(\texttt{GroupTimeSplit}, amendment A-16)", r"(\texttt{GroupTimeSplit})"),
 (r"before being adopted as amendment A-09's frozen training scheme, used throughout", r"before being adopted as the frozen training scheme, used throughout"),
 (r"Amendment A-10 therefore keeps the Gaussian family", r"The frozen protocol therefore keeps the Gaussian family"),
 (r"were closed and pre-registered as amendment A-13 before the confirmatory comparison", r"were closed and pre-registered before the confirmatory comparison"),
 (r"Three findings from the completed experiments (E1, E3, and the observability-overhead runs) shape",
  r"Three findings from the completed experiments (the membership-family ablation, the mandatory baselines and the observability-overhead runs) shape"),
]

MAP_TABLE = r"""\begin{table}[ht]
\caption{Map from the experiment and amendment codes used in the project repository to the sections of the main text and of this file.}\label{tab:code-map}
\small
\begin{tabular}{@{}llp{0.52\linewidth}@{}}
\toprule
Code & Status & Where reported \\
\midrule
E1 & pre-registered, synthetic & Membership family and monotonicity ablation: Section~\ref{subssec4.5}, Table~S2 \\
E3 & pre-registered & Mandatory baselines: Section~\ref{subssec4.3}, Table~\ref{tab:e3-baselines} \\
E4, E4-bis & pre-registered (tag e4-prereg-2026-09-29); E4-bis is the same protocol on the completed 120-asset inventory & Section~\ref{subssec4.3}, Table~\ref{tab:e4-results} \\
E5 & pre-registered sweep & Section~\ref{subssec4.4}, Supplementary note S11 \\
E6 & documented deviation & Section~\ref{sec:e6}, Table~S4, note S3 \\
E7 & pre-registered, OSF-registered forward evaluation & Sections~\ref{subsec:e7} and~\ref{subsec:e7-results}, Tables S9 and S10 \\
E8 & post hoc & Section~\ref{subsec:e8} \\
E9 to E11 & post hoc & Section~\ref{subsec:e9} \\
E14 & post hoc & Section~\ref{subsec:e14}, Table S15, note S9 \\
E15 & post hoc & Section~\ref{subsec:e15}, Tables S5 and S6, note S4 \\
E16 to E19 & post hoc & Section~\ref{subsec:e16}, Tables S7 and S16, note S10 \\
E21 to E24 & post hoc & Section~\ref{subsec:e21}, Table S8, note S6 \\
E25 & unregistered, descriptive & Section~\ref{subsec:e25} \\
E26 & post hoc & Section~\ref{subsec:e26} \\
E27 & descriptive documentation & Section~\ref{subsec:e27}, Tables S11 to S13 \\
Runs 7--16 & protocol external-v3.0 & Section~\ref{subsec4.1}, Table S14, note S8 \\
A-02 & frozen setting & $m_I=3$ for the intermediate variables (Section~\ref{subsec:hanfis-architecture}) \\
A-04 & frozen setting & non-negative consequent slopes through softplus (Section~\ref{subsec:hanfis-architecture}) \\
A-06 & frozen setting & hybrid closed-form/Adam training (Section~\ref{subsec:hanfis-architecture}) \\
A-09 & frozen setting & training configuration: learning rate, ridge, restarts, patience, alternating lower-panel closed form (Section~\ref{subssec4.2}) \\
A-10 & frozen setting & Gaussian family with monotonicity active as default (Section~\ref{subssec4.5}) \\
A-13 & frozen setting & label aggregation, scale and Patch Risk definition (Section~\ref{subsec:target-definition}) \\
A-16 & frozen setting & grouped, embargoed temporal split (Section~\ref{subssec4.2}) \\
\botrule
\end{tabular}
\end{table}
"""


def main():
    raw, crlf = open(P, "rb").read(), b"\r\n" in open(P, "rb").read()
    s = raw.decode("utf-8").replace("\r\n", "\n")
    araw = open(A, "rb").read(); acrlf = b"\r\n" in araw; a = araw.decode("utf-8").replace("\r\n", "\n")
    done_main = "Table~S14 of Additional file~1 gives the paired differences" in s
    done_af = DONE_MARK in a
    if done_main and done_af:
        print("SUDAH TERPASANG: pemadatan dan Additional file 1; tidak ada yang ditulis"); return 0
    if done_main != done_af:
        sys.exit("ABORT: keadaan campuran antara naskah dan Additional file 1; tidak ada yang ditulis")
    find1(a, "\\bibliography{sn-bibliography}", "AF1 bibliography")

    # C.1 metodologi: platform + protokol overhead (satu blok), pengaman validitas (blok kedua)
    pre, b1, post = cut(s, r"\subsection{Experimental platform and telemetry validation}", r"\subsection{Realised exploitability-exposure target", "platform")
    s = pre + PLATFORM_NEW + post
    i = find1(b1, r"\subsection{Observability-Overhead Protocol (external-v3.0)}", "protokol overhead").start()
    proto_old = b1[i:]
    pre, b2, post = cut(s, r"\subsection{Validity safeguards and methodological boundary}", r"\subsection{Prospective evaluation (E7): pre-registered design}", "validitas")
    s = pre + post
    # C.1 hasil overhead
    pre, b3, post = cut(s, r"\subsection{Observability overhead}", r"\subsection{Training configuration}", "hasil overhead")
    s = pre + OVERHEAD_NEW + post
    tab_overhead = take_env(b3, "table", "tab:overhead")
    # C.4 kurva akurasi-kompleksitas
    pre, b4, post = cut(s, r"\subsection{Accuracy-complexity curve}", r"\subsection{Ablation and robustness analysis}", "akurasi-kompleksitas")
    fig_rule = take_env(b4, "figure", "fig:e5-rule-growth"); tab_e5 = take_env(b4, "table", "tab:e5-results")
    s = pre + ACC_NEW.replace("__FIG_RULE_GROWTH__", fig_rule).replace("__TAB_E5__", tab_e5) + post
    acc_note = strip_env(strip_env(b4, "figure", "fig:e5-rule-growth"), "table", "tab:e5-results")
    # C.5 E6
    pre, b5, post = cut(s, r"\subsection{Explanation fidelity (E6)}", r"\subsection{Attribution and monotonicity checks (E8)}", "E6")
    s = pre + E6_NEW + post
    # C.2 E14
    pre, b6, post = cut(s, r"\subsection{Horizon sweep and feature impact by horizon (E14)}", r"\subsection{Prioritisation utility (E15)}", "E14")
    s = pre + E14_NEW + post
    # C.5 E15
    pre, b7, post = cut(s, r"\subsection{Prioritisation utility (E15)}", r"\subsection{Error anatomy and the EPSS model change (E16--E19)}", "E15")
    s = pre + E15_NEW + post
    # C.3 E16-E19
    pre, b8, post = cut(s, r"\subsection{Error anatomy and the EPSS model change (E16--E19)}", r"\subsection{Calibration (E21)}", "E16")
    s = pre + E16_NEW + post
    # C.5 E21
    pre, b9, post = cut(s, r"\subsection{Calibration (E21)}", r"\subsection{Computational cost against flat ANFIS variants (E25)}", "E21")
    s = pre + E21_NEW + post
    # C.7 judul dan amendemen
    for old, new in HEADINGS + AMEND:
        find1(s, old, old[:50]); s = rx(old).sub(lambda m, new=new: new, s, count=1)

    # ---------- Additional file 1 ----------
    def as_note(block, number, title):
        block = re.sub(r"\\subsection\{[^}]*\}\s*", "", block, count=1)
        block = re.sub(r"\\label\{(subsec[^}]*|subssec[^}]*|sec:e6)\}\s*", "", block)
        return f"\\subsection*{{Supplementary note S{number}: {title}}}\n" + block.strip() + "\n\n"
    proto_note = as_note(proto_old, 8, "Observability-overhead protocol (external-v3.0) and validity safeguards (text removed from Section~\\ref{subsec3.2} on 11 November 2026)")
    valid_part = re.sub(r"\\subsection\{[^}]*\}\s*\\label\{subsec:validity\}\s*", "\\\\paragraph{Validity safeguards and methodological boundary.}\n", b2, count=1)
    new_af = (DONE_MARK + "\n"
              "The following material stood in the main text until 11 November 2026 and was moved here so that the main text reports only the "
              "headline numbers. Nothing was re-run; the numbers are those of the original sections.\n\n"
              + tab_overhead + "\n\n" + proto_note + valid_part.strip() + "\n\n"
              + as_note(b6, 9, "Horizon sweep and feature impact by horizon (full text of Section~\\ref{subsec:e14})")
              + as_note(b8, 10, "Error anatomy and the EPSS model change (full text of Section~\\ref{subsec:e16})")
              + as_note(acc_note, 11, "Accuracy-complexity curve (full text of Section~\\ref{subssec4.4})")
              + MAP_TABLE + "\n")
    # label gambar kurva bottleneck tetap di blok yang dipindah (fig:e5-bottleneck-curve, kini Figure S5)
    if "fig:e5-bottleneck-curve" not in new_af or "fig:e5-bottleneck-curve" in s:
        sys.exit("ABORT: gambar kurva bottleneck tidak berpindah dengan benar")
    for lab in ("tab:overhead", "tab:e14", "tab:e19"):
        if ("\\label{" + lab + "}") in s or new_af.count("\\label{" + lab + "}") != 1:
            sys.exit(f"ABORT: label {lab} tidak berpindah dengan benar")
    a = a.replace("\\bibliography{sn-bibliography}", new_af + "\\bibliography{sn-bibliography}", 1)

    open(P + ".pre-condense.bak", "wb").write(raw); open(A + ".pre-condense.bak", "wb").write(araw)
    open(P, "wb").write((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
    open(A, "wb").write((a.replace("\n", "\r\n") if acrlf else a).encode("utf-8"))
    print("OK pemadatan C.1 sampai C.7 |", "CRLF" if crlf else "LF", "| cadangan .pre-condense.bak")
    return 0


if __name__ == "__main__":
    sys.exit(main())
