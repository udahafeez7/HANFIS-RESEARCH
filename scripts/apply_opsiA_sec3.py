#!/usr/bin/env python3
"""Opsi A: ganti blok protokol telemetri lama (Run 1-5, checkpoint B4.11B) dengan
deskripsi external-v3.0 (Run 7-16). Gagal-tertutup: semua jangkar harus tepat 1 kali,
jika tidak, tidak ada yang ditulis. Idempoten (berhenti bila sudah diterapkan)."""
import sys, hashlib, shutil, pathlib
P = pathlib.Path("manuscript/sn-article.tex")
s = P.read_text(encoding="utf-8")
MARK = r"\label{subsec:overhead-protocol}"
if MARK in s:
    print("Sudah diterapkan; tidak ada perubahan."); sys.exit(0)

def one(sub):
    n = s.count(sub)
    if n != 1:
        sys.exit(f"ABORT: jangkar ditemukan {n}x (harus 1): {sub[:70]!r}")
    return s.index(sub)

# --- Blok A: Dataset Construction (telemetri lama) -> protokol external-v3.0 baru
a0 = one("\\subsection{Dataset Construction and Target Definition}\n\\label{subsec3.3}")
a1 = one("\\subsection{Realised Exploitability-Exposure Target and Real-World Asset-Week Dataset}")
assert a0 < a1
NEW_A = r"""\subsection{Observability-Overhead Protocol (external-v3.0)}
\label{subsec:overhead-protocol}

The gates and integrity controls of Table~\ref{tab1} were developed during the first runs and were carried forward unchanged into protocol \texttt{external-v3.0}, which produced all observability-overhead results reported in Section~\ref{subsec4.1}. The protocol comprises ten complete counterbalanced ON--OFF pairs (Runs~7--16): Runs~8, 10, 12, 14 and~16 were executed OFF--ON, and Runs~7, 9, 11, 13 and~15 ON--OFF. The earlier Runs~1--6 belong to the protocol-development phase and are not pooled with the ten pairs. One aborted attempt of Run~7 and one aborted attempt of Run~17 failed the integrity gate and are recorded as incidents rather than observations.

The protocol follows a fail-closed rule: a condition is admitted to measurement only when the nodes, the P0 workload (two of two replicas), the HTTP service (status~200) and the required monitoring state satisfy the acceptance criteria of Table~\ref{tab1}; a failed gate yields a \texttt{HOLD} decision, not an observation. Each run is archived with a SHA-256 manifest, so that the ten run archives and the cumulative analysis can be re-verified without reconstructing the original command sequence.

Telemetry preserves the link between each value and its Kubernetes object, node, container, condition and run. The measurements are node-, pod- and container-level CPU and memory, pod readiness, HTTP outcome and response latency; identical request-generation and sampling procedures are applied in the ON and OFF conditions. Configuration files, event logs, gate reports and manifests document how each observation was produced and are not treated as HANFIS training features.

Let $Y_{r,c,k}$ denote observation $k$ of run $r$ under condition $c\in\{\mathrm{ON},\mathrm{OFF}\}$, where $Y$ may be CPU, memory or latency. The run mean is
\begin{equation}
 \bar{Y}_{r,c}=\frac{1}{n_{r,c}}\sum_{k=1}^{n_{r,c}}Y_{r,c,k},
\end{equation}
the paired absolute overhead is $\Delta Y_r=\bar{Y}_{r,\mathrm{ON}}-\bar{Y}_{r,\mathrm{OFF}}$, and the relative overhead, when the OFF denominator is non-zero, is
\begin{equation}
 \Delta Y^{(\%)}_r=\frac{\bar{Y}_{r,\mathrm{ON}}-\bar{Y}_{r,\mathrm{OFF}}}{\bar{Y}_{r,\mathrm{OFF}}}\times100\%.
\end{equation}
The run, not the individual sample, is the independent replication unit, which avoids pseudoreplication from temporally adjacent samples. Inference over the ten paired differences uses an exact two-sided sign-flip test, whose smallest attainable $p$ with ten pairs is $2/2^{10}=0.002$, together with a bootstrap confidence interval for the mean difference. Effect sizes, confidence intervals and the consistency of direction carry more interpretive weight than a binary significance decision. The estimated increment is an instrumentation cost; it must not be read as a change in application exposure.

"""
s = s[:a0] + NEW_A + s[a1:]

# --- Blok B: Model Training and Evaluation Protocol (versi overhead lama) -> dihapus
b0 = one("\\subsection{Model Training and Evaluation Protocol}\n\\label{subsec3.4}")
b1 = one("\\subsection{Integration of Validated Telemetry with HANFIS}")
assert b0 < b1
s = s[:b0] + s[b1:]

# --- Blok C: Audit lima pertanyaan + Validity (checkpoint B4.11B) -> validity ringkas
c0 = one("\\subsection{Audit of the Five Methodological Questions}")
c1 = one("\\section{Results}\\label{sec4}")
assert c0 < c1
NEW_C = r"""\subsection{Validity Safeguards and Methodological Boundary}
\label{subsec:validity}

Internal validity rests on paired comparisons, a stable workload, condition gates, health checks, counterbalanced order, and the rejection of measurements taken under invalid states. Construct validity is protected by separating observability overhead from cybersecurity exposure and by requiring a semantic mapping before any telemetry variable is used as a HANFIS feature. Reliability is supported by script-based execution, frozen configuration and cryptographic integrity checks, and traceability runs from raw samples through summaries to model-ready features.

Several limits remain. WSL~2 with Docker Desktop is reproducible but does not represent every production Kubernetes deployment, and the two-node topology and P0 workload constrain external validity. Ten pairs make an effect-size reading appropriate, but they bound the smallest attainable sign-flip $p$ at $0.002$ and give limited power for small latency effects. The protocol was frozen before the ten pairs were analysed, yet its version is entangled with the platform on which the earlier runs were taken, so cross-platform comparisons are descriptive. Finally, successful telemetry collection does not by itself show predictive value for cyber risk; that claim rests on the held-out HANFIS evaluation against the baselines of Section~\ref{sec4}.

"""
s = s[:c0] + NEW_C + s[c1:]

# --- Penyelarasan teks basi
for old, new in [
 ("The experiment comprises five paired runs. Conditions", "The observability experiment comprises ten paired runs (Runs~7--16). Conditions"),
 ("child{node{Five paired runs}}", "child{node{Ten paired runs}}"),
 ("Five paired observability runs, while showing large", "Ten paired observability runs, while showing large"),
]:
    one(old); s = s.replace(old, new)

shutil.copy(P, str(P) + ".pre-opsiA.bak")
P.write_text(s, encoding="utf-8")
print("OK. sha256 baru:", hashlib.sha256(s.encode()).hexdigest()[:16])
