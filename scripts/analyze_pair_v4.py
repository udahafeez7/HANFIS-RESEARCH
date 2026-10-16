#!/usr/bin/env python3
"""analyze_pair_v4.py - descriptive analyzer for ONE protocol-v4.2.x run pair (ON/OFF).

Written 2026-10-16 for Run 17 (attempt 2). Replaces analyze_pair_v3.py, which assumes
32 samples per condition and the v3 directory layout. It follows
protocols/RUN17_ANALYSIS_NOTE_2026-10-16.md:

  * the inferential unit is one complete run pair, never one request;
  * with ONE pair, the run-level confidence interval is undefined (NaN) and the
    exact sign-flip p-value is 1.0; no hypothesis test is run;
  * everything below is DESCRIPTIVE (guard P11: no causal claim about observability overhead);
  * an optional request-level bootstrap is shown only as within-run precision, labeled
    "descriptive, not inferential".

What it reads
  http.csv   columns: seq,timestamp_utc,http_code,time_namelookup,time_connect,
             time_starttransfer,time_total,size_bytes   (time_* in seconds, as written by curl)
  other *.csv in a condition directory (server samples): every numeric column is
             summarized as n / mean / median / max. The column names are NOT assumed.

Usage
  python3 analyze_pair_v4.py --on-dir <dir with ON files> --off-dir <dir with OFF files> \
          [--out report.json] [--bootstrap 20000] [--seed 20260829] [--pair-name NAME]

  Or, if the pair directory holds exactly one ON and one OFF subdirectory:
  python3 analyze_pair_v4.py --pair-dir <RunsV4/run17-on-off-...>

Guard: when a path contains "RunsV4" (real data), the script refuses to run unless the
analysis-unit note exists in git history (--repo <repo root>), or --skip-note-check is given.
The commit timestamp of that note is the pre-specification proof.

Only numpy and the standard library are required. No file is modified.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

NOTE_REL = "protocols/RUN17_ANALYSIS_NOTE_2026-10-16.md"
HTTP_COLS = ("seq", "http_code", "time_total")
DEFAULT_BOOT = 20000
DEFAULT_SEED = 20260829
PCTS = (50, 95, 99)


# ----------------------------------------------------------------- helpers
def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return math.nan
    return v if math.isfinite(v) else math.nan


def read_csv(path: Path):
    with path.open(newline="") as fh:
        rd = csv.DictReader(fh)
        rows = list(rd)
        return rd.fieldnames or [], rows


def pct(a, q):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return float(np.percentile(a, q, method="linear")) if a.size else math.nan


def describe(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    if not a.size:
        return {"n": 0, "mean": math.nan, "median": math.nan, "p95": math.nan, "p99": math.nan}
    return {
        "n": int(a.size),
        "mean": float(a.mean()),
        "median": pct(a, 50),
        "p95": pct(a, 95),
        "p99": pct(a, 99),
    }


def exact_sign_flip_p(diffs):
    """Two-sided exact sign-flip p for the mean of per-pair differences (n pairs)."""
    d = np.asarray([x for x in diffs if math.isfinite(x)], float)
    n = d.size
    if n == 0:
        return math.nan
    obs = abs(d.mean())
    if obs == 0.0:
        return 1.0
    count = 0
    for mask in range(1 << n):
        s = np.array([1.0 if (mask >> i) & 1 else -1.0 for i in range(n)])
        if abs((s * d).mean()) >= obs - 1e-15:
            count += 1
    return count / (1 << n)


def boot_ci(a, reps, seed):
    """Percentile bootstrap of the mean over REQUESTS within one run (descriptive only)."""
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    if a.size < 2 or reps <= 0:
        return (math.nan, math.nan)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, a.size, size=(reps, a.size))
    m = a[idx].mean(axis=1)
    return (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


# ------------------------------------------------------------- loaders
def load_http(dirpath: Path):
    p = dirpath / "http.csv"
    if not p.exists():
        raise SystemExit(f"ERROR: {p} not found")
    cols, rows = read_csv(p)
    missing = [c for c in HTTP_COLS if c not in cols]
    if missing:
        raise SystemExit(f"ERROR: {p} lacks columns {missing}; has {cols}")
    seq = [int(float(r["seq"])) for r in rows]
    code = [fnum(r["http_code"]) for r in rows]
    t = [fnum(r["time_total"]) for r in rows]
    return {"seq": seq, "code": code, "t": t, "n_rows": len(rows), "path": str(p)}


def ok_mask(code, t):
    return np.array([(c == 200.0) and math.isfinite(x) and x > 0 for c, x in zip(code, t)])


SKIP_COLS = {"seq"}


def _num_cols(cols, rows):
    out = {}
    for c in cols:
        if c in SKIP_COLS:
            continue
        v = np.array([fnum(r.get(c)) for r in rows], float)
        good = v[np.isfinite(v)]
        if good.size and good.size >= 0.5 * max(len(rows), 1):
            out[c] = good
    return out


def _stat(good):
    return {"n": int(good.size), "mean": float(good.mean()),
            "median": pct(good, 50), "max": float(good.max())}


def server_summary(dirpath: Path):
    """Every non-http CSV: numeric columns as n/mean/median/max. If the file has a 'group'
    column, the statistics are computed per group (e.g. p0 vs monitoring). Column names are
    not assumed; 'seq' is skipped."""
    out = {}
    for p in sorted(dirpath.glob("*.csv")):
        if p.name == "http.csv":
            continue
        cols, rows = read_csv(p)
        info = {"n_rows": len(rows), "columns": {}, "by_group": {}}
        if "group" in cols:
            groups = sorted({r["group"] for r in rows})
            for g in groups:
                sub = [r for r in rows if r["group"] == g]
                info["by_group"][g] = {c: _stat(v) for c, v in _num_cols(cols, sub).items()}
        else:
            info["columns"] = {c: _stat(v) for c, v in _num_cols(cols, rows).items()}
        out[p.name] = info
    return out


# ------------------------------------------------------------- analysis
def condition_block(h):
    t = np.array(h["t"], float)
    ok = ok_mask(h["code"], h["t"])
    ms = t[ok] * 1000.0
    return {
        "n_requests": h["n_rows"],
        "n_ok": int(ok.sum()),
        "failure_rate": float(1.0 - ok.sum() / h["n_rows"]) if h["n_rows"] else math.nan,
        "latency_ms": describe(ms),
        "ok_ms": ms,
    }


def analyze(on_dir: Path, off_dir: Path, reps: int, seed: int, name: str):
    on, off = load_http(on_dir), load_http(off_dir)
    con, coff = condition_block(on), condition_block(off)

    # pair by sequence id; only seq present and OK in both conditions
    mon = {s: x for s, x, c in zip(on["seq"], on["t"], on["code"]) if c == 200.0 and math.isfinite(x) and x > 0}
    mof = {s: x for s, x, c in zip(off["seq"], off["t"], off["code"]) if c == 200.0 and math.isfinite(x) and x > 0}
    common = sorted(set(mon) & set(mof))
    d_ms = np.array([(mon[s] - mof[s]) * 1000.0 for s in common], float)

    stat_diff = {}
    for k in ("mean", "median", "p95", "p99"):
        a, b = con["latency_ms"][k], coff["latency_ms"][k]
        stat_diff[k] = a - b if math.isfinite(a) and math.isfinite(b) else math.nan

    paired = {
        "n_pairs_by_seq": int(d_ms.size),
        "n_seq_dropped": int(max(on["n_rows"], off["n_rows"]) - d_ms.size),
        "mean_diff_ms": float(d_ms.mean()) if d_ms.size else math.nan,
        "median_diff_ms": pct(d_ms, 50),
        "p05_diff_ms": pct(d_ms, 5),
        "p95_diff_ms": pct(d_ms, 95),
    }
    lo, hi = boot_ci(d_ms, reps, seed)
    paired["request_level_bootstrap_95ci_of_mean_diff_ms"] = {
        "lo": lo, "hi": hi, "reps": reps, "seed": seed,
        "label": "DESCRIPTIVE within-run precision; not inferential; not a test of the registered hypothesis",
    }

    n_pairs_runlevel = 1
    run_level = {
        "n_run_pairs": n_pairs_runlevel,
        "run_level_ci": {"lo": math.nan, "hi": math.nan, "note": "undefined for n<2 (bootstrap needs >=2 run pairs)"},
        "exact_sign_flip_p": exact_sign_flip_p([paired["mean_diff_ms"]]),
        "note": "n=1: p=1.0 by construction; NO hypothesis test is run on Run 17 alone (analysis-unit note, decision 2)",
        "min_attainable_two_sided_p": {str(n): 2.0 / 2 ** n for n in (1, 2, 4, 5, 6, 10)},
    }

    result = {
        "pair_name": name,
        "script": "analyze_pair_v4.py",
        "scope": "descriptive; protocol v4.2.x; ON-OFF only (treatment order and period confounded); guard P11",
        "on": {k: v for k, v in con.items() if k != "ok_ms"},
        "off": {k: v for k, v in coff.items() if k != "ok_ms"},
        "on_minus_off_stat_diff_ms": stat_diff,
        "paired_by_seq": paired,
        "run_level": run_level,
        "server_on": server_summary(on_dir),
        "server_off": server_summary(off_dir),
        "input_files": {"on_http": on["path"], "off_http": off["path"]},
    }
    return result


# ------------------------------------------------------------- guards / CLI
def note_committed(repo: Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo), "log", "--format=%H %cI", "--", NOTE_REL],
            capture_output=True, text=True, timeout=30,
        )
    except Exception:
        return False
    return r.returncode == 0 and bool(r.stdout.strip())


def find_condition_dirs(pair_dir: Path):
    dirs = sorted({p.parent for p in pair_dir.rglob("http.csv")})
    on = [d for d in dirs if d.name.lower().startswith("on")]
    off = [d for d in dirs if d.name.lower().startswith("off")]
    if len(on) != 1 or len(off) != 1:
        raise SystemExit(
            "ERROR: could not identify exactly one ON and one OFF directory (names starting with "
            f"'on'/'off') under {pair_dir}; found on={on}, off={off}. Pass --on-dir and --off-dir."
        )
    return on[0], off[0]


def fmt(x, nd=2):
    return "nan" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.{nd}f}"


def print_report(r):
    print(f"PAIR: {r['pair_name']}")
    print(f"SCOPE: {r['scope']}")
    print()
    print(f"{'':10s}{'n_req':>7s}{'n_ok':>7s}{'fail%':>8s}{'mean':>10s}{'median':>10s}{'p95':>10s}{'p99':>10s}   (latency, ms)")
    for k in ("off", "on"):
        c = r[k]; L = c["latency_ms"]
        print(f"{k.upper():10s}{c['n_requests']:7d}{c['n_ok']:7d}{100*c['failure_rate']:8.2f}"
              f"{fmt(L['mean']):>10s}{fmt(L['median']):>10s}{fmt(L['p95']):>10s}{fmt(L['p99']):>10s}")
    d = r["on_minus_off_stat_diff_ms"]
    print(f"{'ON-OFF':10s}{'':7s}{'':7s}{'':8s}{fmt(d['mean']):>10s}{fmt(d['median']):>10s}{fmt(d['p95']):>10s}{fmt(d['p99']):>10s}")
    p = r["paired_by_seq"]; b = p["request_level_bootstrap_95ci_of_mean_diff_ms"]
    print()
    print(f"Paired by seq: n={p['n_pairs_by_seq']}, mean diff {fmt(p['mean_diff_ms'])} ms, "
          f"median diff {fmt(p['median_diff_ms'])} ms, [p05,p95] [{fmt(p['p05_diff_ms'])}, {fmt(p['p95_diff_ms'])}]")
    print(f"Request-level bootstrap 95% interval of the mean diff: [{fmt(b['lo'])}, {fmt(b['hi'])}] ms "
          f"({b['reps']} reps, seed {b['seed']}) - {b['label']}")
    rl = r["run_level"]
    print()
    print(f"Run level: n pairs = {rl['n_run_pairs']}; CI = NaN; exact sign-flip p = {rl['exact_sign_flip_p']}. {rl['note']}")
    print("Interpretation guard: description only; ON-OFF order confounded; no causal claim (P11).")
    for side in ("off", "on"):
        s = r[f"server_{side}"]
        if s:
            print(f"\nServer files ({side.upper()}):")
            for fn, info in s.items():
                print(f"  {fn}: {info['n_rows']} rows")
                for c, v in info["columns"].items():
                    print(f"    {c}: mean {fmt(v['mean'],4)}  median {fmt(v['median'],4)}  max {fmt(v['max'],4)}  (n={v['n']})")
                for g, cs in info["by_group"].items():
                    for c, v in cs.items():
                        print(f"    [{g}] {c}: mean {fmt(v['mean'],4)}  median {fmt(v['median'],4)}  max {fmt(v['max'],4)}  (n={v['n']})")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pair-dir")
    ap.add_argument("--on-dir")
    ap.add_argument("--off-dir")
    ap.add_argument("--out")
    ap.add_argument("--bootstrap", type=int, default=DEFAULT_BOOT)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--pair-name", default="")
    ap.add_argument("--repo", default=".", help="git repo root, used for the note-committed guard")
    ap.add_argument("--skip-note-check", action="store_true")
    a = ap.parse_args(argv)

    if a.pair_dir:
        on_dir, off_dir = find_condition_dirs(Path(a.pair_dir))
        name = a.pair_name or Path(a.pair_dir).name
    elif a.on_dir and a.off_dir:
        on_dir, off_dir = Path(a.on_dir), Path(a.off_dir)
        name = a.pair_name or f"{on_dir} vs {off_dir}"
    else:
        ap.error("give --pair-dir, or both --on-dir and --off-dir")

    real = "RunsV4" in str(on_dir) or "RunsV4" in str(off_dir)
    if real and not a.skip_note_check and not note_committed(Path(a.repo)):
        sys.exit(
            f"REFUSED: {NOTE_REL} has no commit in {a.repo}. Commit the analysis-unit note first "
            "(its commit time is the pre-specification proof), then rerun."
        )

    res = analyze(on_dir, off_dir, a.bootstrap, a.seed, name)
    print_report(res)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=2, allow_nan=True))
        print(f"\nWrote {a.out}")


if __name__ == "__main__":
    main()
