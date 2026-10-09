#!/usr/bin/env python3
"""E7 -- pelaksana D2 satu-langkah (bagian 4 protokol E7). Hanya MENJALANKAN skrip beku dalam urutan wajib dan berhenti di kegagalan pertama; tidak menghitung apa pun sendiri.
Tahap: fetch -> rescan -> build -> predict -> evaluate (atau --stage all). Sebelum tahap apa pun (kecuali --dry-run) verify_prereg_tag.py harus LOLOS untuk tag dan seluruh artefak beku.
Pagar: D2 harus hari Senin dan menghasilkan >= 6 minggu uji matang (jika tidak: STATUS=HOLD_E7_TOO_FEW_WEEKS; D2 cadangan hanya dipilih SEBELUM model dijalankan, tidak diputuskan di sini);
fetch dan rescan menolak berjalan sebelum D2; tiap tahap menolak berjalan bila tahap sebelumnya belum selesai; tahap evaluate menolak bila sudah ada e7_results_*.json (dijalankan SEKALI).
  python scripts/e7_d2.py --d2 2026-11-02 --tag e7-prereg-2026-10-20 --dry-run          (tanpa eksekusi; boleh sebelum pembekuan)
  python scripts/e7_d2.py --d2 2026-11-02 --tag e7-prereg-2026-10-20 --stage all"""
import argparse, datetime as dt, glob, json, re, subprocess, sys
from pathlib import Path

FFW, FIRST_SNAP, TABLE_START, MIN_WEEKS = "2026-08-31", "2026-09-28", "2025-08-25", 6
STATUS_START = "2025-08-25"   # fetch_snapshots.py status exige --start/--end (visto em --help); cobre a janela selada inteira
LAMBDA, OUT, PREFIX = "protocols/E7_lambda_2026-10-08.json", "results_python/e7", "data/processed/asset_weeks_v3"
STAGES = ["fetch", "rescan", "build", "predict", "evaluate"]
STATIC = ["protocols/E7_lambda_2026-10-08.json", "results_python/e7_final/final_models_manifest.json", "scripts/e7_pipeline.py", "scripts/e7_evaluate.py", "scripts/e7_rescan.py", "scripts/verify_prereg_tag.py",
          "scripts/make_prereg_tag.py", "scripts/fetch_snapshots.py", "scripts/build_asset_weeks.py", "scripts/e4_run.py", "scripts/scan_image_evidence.sh", "scripts/e7_d2.py",
          "python_hanfis/hanfis_end2end.py", "python_hanfis/splits.py", "configs/assets.csv"]


def plan(a, root):
    d2 = dt.date.fromisoformat(a.d2)
    if d2.weekday() != 0: sys.exit(f"ABORT: D2 {a.d2} bukan hari Senin")
    last = d2 - dt.timedelta(days=28); first = dt.date.fromisoformat(FFW); n = (last - first).days // 7 + 1 if last >= first else 0
    m = re.fullmatch(r"e7-prereg-(\d{4}-\d{2}-\d{2})", a.tag or "")
    if not m: sys.exit("ABORT: --tag harus berbentuk e7-prereg-YYYY-MM-DD")
    frozen = [f"protocols/E7_preregistration_{m.group(1)}.md"] + STATIC + sorted(str(p.relative_to(root)) for p in (root / "results_python/e7_final/models").glob("final_seed*_hanfis.pt"))
    pred, diag = f"{OUT}/forward_predictions_{a.d2}.csv", f"{OUT}/forward_diagnostics_{a.d2}.csv"; py = a.py
    cmds = {"fetch": [[py, "scripts/fetch_snapshots.py", "fetch", "--start", FIRST_SNAP, "--end", a.d2], [py, "scripts/fetch_snapshots.py", "status", "--start", STATUS_START, "--end", a.d2], [py, "scripts/fetch_snapshots.py", "verify"]],
            "rescan": [[py, "scripts/e7_rescan.py", "--d2", a.d2, "--download-db"]],
            "build": [[py, "scripts/build_asset_weeks.py", "--assets", "configs/assets_v3.csv", "--snapshots", "data/real/snapshots", "--out-prefix", PREFIX, "--start", TABLE_START, "--end", str(last)]],
            "predict": [[py, "scripts/e7_pipeline.py", "predict", "--table", PREFIX + ".csv", "--models-dir", "results_python/e7_final", "--first-week", FFW, "--last-week", str(last), "--out", pred, "--diagnostics", diag]],
            "evaluate": [[py, "scripts/e7_evaluate.py", "--run", "--pred", pred, "--lambda-json", LAMBDA, "--tag", a.tag, "--files", *frozen]]}
    return d2, last, n, frozen, cmds


def run(cmd, root, log):
    print("$ " + " ".join(cmd[:12]) + (" ..." if len(cmd) > 12 else "")); p = subprocess.Popen(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True); out = []
    for line in p.stdout: print(line, end=""); log.write(line); out.append(line)
    return p.wait(), "".join(out)


def matured_weeks(table):
    import pandas as pd
    d = pd.read_csv(table, usecols=["week_start_utc", "y"]); d["w"] = pd.to_datetime(d["week_start_utc"], utc=True).dt.strftime("%Y-%m-%d")
    return sorted(w for w, g in d.groupby("w") if w >= FFW and g["y"].notna().any())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--d2", required=True); ap.add_argument("--tag", required=True); ap.add_argument("--stage", choices=STAGES + ["all"]); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--redo", choices=STAGES[:-1]); ap.add_argument("--root", default="."); ap.add_argument("--py", default=sys.executable); ap.add_argument("--today", default=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args(argv); root = Path(a.root).resolve(); d2, last, n, frozen, cmds = plan(a, root)
    print(f"D2={a.d2}; minggu uji {FFW} .. {last} = {n} minggu (minimum {MIN_WEEKS}); artefak beku: {len(frozen)}; tag: {a.tag}")
    if n < MIN_WEEKS: print(f"STATUS=HOLD_E7_TOO_FEW_WEEKS ({n} < {MIN_WEEKS}); E7 ditunda, kriteria tidak dilonggarkan"); return 3
    todo = STAGES if a.stage == "all" else ([a.stage] if a.stage else [])
    if a.dry_run or not todo:
        for s in (todo or STAGES):
            for c in cmds[s]: print(f"[{s}] " + " ".join(c[:14]) + (" ..." if len(c) > 14 else ""))
        print("STATUS=E7_D2_DRY_RUN (tidak ada yang dijalankan)"); return 0
    stp = root / OUT / "d2_state.json"; stp.parent.mkdir(parents=True, exist_ok=True); st = json.loads(stp.read_text()) if stp.exists() else {}
    if a.redo: st.pop(a.redo, None)
    v = subprocess.run([a.py, "scripts/verify_prereg_tag.py", a.tag, *frozen], cwd=root, capture_output=True, text=True); print(v.stdout.strip())
    if v.returncode != 0: print("STATUS=HOLD_E7_PREREG_NOT_VERIFIED"); return 2
    for s in todo:
        if s in st and s != "evaluate": print(f"[{s}] sudah selesai ({st[s]['selesai_utc']}); lewati (pakai --redo {s} bila sengaja)"); continue
        prev = STAGES[STAGES.index(s) - 1] if STAGES.index(s) else None
        if prev and prev not in st: print(f"STATUS=HOLD_E7_D2_ORDER ({s} menunggu {prev})"); return 2
        if s in ("fetch", "rescan") and a.today < a.d2: print(f"STATUS=HOLD_E7_D2_NOT_YET ({s}: hari ini {a.today} < D2 {a.d2})"); return 2
        if s == "evaluate" and list((root / OUT).glob("e7_results_*.json")): print("STATUS=HOLD_E7_ALREADY_RUN (e7_evaluate --run dijalankan SEKALI; hasil sudah ada)"); return 2
        logd = root / OUT / "d2_logs"; logd.mkdir(parents=True, exist_ok=True); stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        with open(logd / f"{s}_{stamp}.log", "w", encoding="utf-8") as lg:
            for c in cmds[s]:
                rc, text = run(c, root, lg)
                if rc != 0: print(f"STATUS=HOLD_E7_D2_STAGE_FAILED ({s}, kode {rc}); tahap berikutnya tidak dijalankan"); return 2
                if s == "build" and "STATUS=TRAINING_AUTHORIZED" not in text: print("STATUS=HOLD_E7_D2_BUILD_GATE (gerbang data tidak TRAINING_AUTHORIZED)"); return 2
        if s == "build":
            w = matured_weeks(root / (PREFIX + ".csv")); print(f"minggu uji matang pada tabel v3: {len(w)} ({', '.join(w)})")
            if len(w) < MIN_WEEKS: print(f"STATUS=HOLD_E7_TOO_FEW_WEEKS ({len(w)} < {MIN_WEEKS})"); return 3
        st[s] = {"selesai_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "log": f"{s}_{stamp}.log"}; stp.write_text(json.dumps(st, indent=1))
    print("STATUS=E7_D2_STAGES_DONE: " + ", ".join(todo)); return 0


if __name__ == "__main__":
    sys.exit(main())
