#!/usr/bin/env python3
"""E4 / E4-bis result figures (manuscript §4.4).

Reads the two artefacts written by scripts/e4_run.py + scripts/e4_analyse.py:

  <results_dir>/E4_skill_scores_<ts>.csv
      columns: ref,hypothesis,ss_point,ci_lo,ci_hi,sesoi_or_margin,
               p_boot_at_margin,n_boot_valid,p_holm,confirmed
  <results_dir>/predictions_<ts>.csv
      columns: event_id,image_id,fold,y_true,y_hanfis,y_cvss_only,
               y_persistence,y_ridge_7inputs,y_matched,y_flat_full

and writes three figures (PDF + PNG, deterministic names):

  fig_e4_skill_forest.{pdf,png}   skill score vs each baseline, 95% CI,
                                  SESOI / margin line, Holm p, confirmed flag
  fig_e4_skill_per_fold.{pdf,png} per-fold skill score 1 - MSE_h/MSE_b per
                                  baseline (the paired per-fold comparison)
  fig_e4_pred_vs_true.{pdf,png}   HANFIS held-out prediction vs label,
                                  coloured by fold, 1:1 line

Latest timestamp of each artefact is used unless --skill-scores /
--predictions are given explicitly. The script is read-only w.r.t. inputs,
fail-closed on missing files or columns, and never silently substitutes.

Usage:
  python scripts/e4_figures.py --results-dir results_python/e4bis_120 \
      --out-dir manuscript/figures/e4bis --tag e4bis
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SKILL_COLS = [
    "ref", "hypothesis", "ss_point", "ci_lo", "ci_hi", "sesoi_or_margin",
    "p_boot_at_margin", "n_boot_valid", "p_holm", "confirmed",
]
PRED_COLS = [
    "event_id", "image_id", "fold", "y_true", "y_hanfis", "y_cvss_only",
    "y_persistence", "y_ridge_7inputs", "y_matched", "y_flat_full",
]
# baseline column -> (ref name in skill table, display label)
BASELINES = {
    "y_persistence": ("persistence", "Persistence (lag 4 wk)"),
    "y_cvss_only": ("cvss_only", "CVSS only"),
    "y_ridge_7inputs": ("ridge_7inputs", "Ridge, 7 inputs"),
    "y_matched": ("matched", "Flat ANFIS (param-matched)"),
    "y_flat_full": ("flat_full", "Flat ANFIS (full, reference)"),
}
# Display order: strongest baseline first (persistence is the real bar).
REF_ORDER = ["persistence", "ridge_7inputs", "matched", "cvss_only", "flat_full"]

TS_RE = re.compile(r"_(\d{8}T\d{6}Z)\.csv$")


class FigureInputError(RuntimeError):
    pass


def _latest(results_dir: Path, prefix: str) -> Path:
    cands = sorted(results_dir.glob(f"{prefix}_*.csv"), key=lambda p: TS_RE.search(p.name).group(1) if TS_RE.search(p.name) else "")
    cands = [p for p in cands if TS_RE.search(p.name)]
    if not cands:
        raise FigureInputError(f"no {prefix}_<timestamp>.csv in {results_dir}")
    return cands[-1]


def _require_cols(df: pd.DataFrame, cols: list[str], what: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise FigureInputError(f"{what}: missing columns {missing}; have {list(df.columns)}")


def load_inputs(results_dir: Path, skill_path: Path | None, pred_path: Path | None):
    skill_path = skill_path or _latest(results_dir, "E4_skill_scores")
    pred_path = pred_path or _latest(results_dir, "predictions")
    for p in (skill_path, pred_path):
        if not p.is_file():
            raise FigureInputError(f"input not found: {p}")
    skill = pd.read_csv(skill_path)
    pred = pd.read_csv(pred_path)
    _require_cols(skill, SKILL_COLS, skill_path.name)
    _require_cols(pred, PRED_COLS, pred_path.name)
    if skill.empty:
        raise FigureInputError(f"{skill_path.name} has no rows")
    if pred.empty:
        raise FigureInputError(f"{pred_path.name} has no rows")
    skill["confirmed"] = skill["confirmed"].astype(str).str.lower().isin(["true", "1", "yes"])
    return skill, pred, skill_path, pred_path


def per_fold_skill(pred: pd.DataFrame) -> pd.DataFrame:
    """SS_b(fold) = 1 - MSE(hanfis)/MSE(baseline) on labelled rows of that fold."""
    rows = []
    d = pred.dropna(subset=["y_true", "y_hanfis"])
    for fold, g in d.groupby("fold", sort=True):
        for col, (ref, _) in BASELINES.items():
            gb = g.dropna(subset=[col])
            if gb.empty:
                continue
            mse_b = np.mean((gb["y_true"] - gb[col]) ** 2)
            mse_h = np.mean((gb["y_true"] - gb["y_hanfis"]) ** 2)
            ss = np.nan if mse_b == 0 else 1.0 - mse_h / mse_b
            rows.append({"fold": int(fold), "ref": ref, "n": len(gb), "mse_hanfis": mse_h, "mse_baseline": mse_b, "ss": ss})
    out = pd.DataFrame(rows)
    if out.empty:
        raise FigureInputError("no labelled rows to compute per-fold skill")
    return out


def _order(refs: list[str]) -> list[str]:
    known = [r for r in REF_ORDER if r in refs]
    extra = sorted(r for r in refs if r not in REF_ORDER)
    return known + extra


def fig_forest(skill: pd.DataFrame, out: Path, tag: str) -> None:
    sk = skill.set_index("ref")
    refs = _order(list(sk.index))
    fig, ax = plt.subplots(figsize=(6.0, 0.6 * len(refs) + 1.2))
    y = np.arange(len(refs))[::-1]
    for yi, ref in zip(y, refs):
        r = sk.loc[ref]
        label = {v[0]: v[1] for v in BASELINES.values()}.get(ref, ref)
        colour = "#1b7837" if bool(r["confirmed"]) else "#636363"
        ax.errorbar(r["ss_point"], yi, xerr=[[r["ss_point"] - r["ci_lo"]], [r["ci_hi"] - r["ss_point"]]],
                    fmt="o", color=colour, ecolor=colour, elinewidth=1.4, capsize=3, markersize=5)
        m = r["sesoi_or_margin"]
        if pd.notna(m):
            ax.plot([m, m], [yi - 0.3, yi + 0.3], ls="--", lw=0.9, color="#b2182b")
        verdict = "confirmed" if bool(r["confirmed"]) else "not confirmed"
        txt = (f"{r['hypothesis']}: SS={r['ss_point']:.3f} [{r['ci_lo']:.3f}, {r['ci_hi']:.3f}], "
               f"p_Holm={r['p_holm']:.3f}, {verdict}")
        ax.annotate(txt, xy=(1.02, yi), xycoords=("axes fraction", "data"), va="center", fontsize=7.5)
        ax.text(-0.02, yi, label, ha="right", va="center", fontsize=8.5, transform=ax.get_yaxis_transform())
    ax.axvline(0.0, color="black", lw=0.8)
    ax.set_yticks([])
    ax.set_xlabel("Skill score, 1 − MSE$_{HANFIS}$/MSE$_{baseline}$ (95% bootstrap CI)", fontsize=8.5)
    lo = min(0.0, float(np.nanmin(sk["ci_lo"])) - 0.05)
    hi = max(1.0, float(np.nanmax(sk["ci_hi"])) + 0.05)
    ax.set_xlim(lo, hi)
    ax.set_title(f"E4 confirmatory skill scores ({tag}); dashed red = SESOI/margin", fontsize=9)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    fig.subplots_adjust(left=0.30, right=0.58, top=0.85, bottom=0.22)
    _save(fig, out / "fig_e4_skill_forest")


def fig_per_fold(pf: pd.DataFrame, skill: pd.DataFrame, out: Path, tag: str) -> None:
    refs = _order(sorted(pf["ref"].unique()))
    folds = sorted(pf["fold"].unique())
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    width = 0.8 / max(1, len(refs))
    x = np.arange(len(folds))
    labels = {v[0]: v[1] for v in BASELINES.values()}
    sk = skill.set_index("ref")
    for i, ref in enumerate(refs):
        s = pf[pf.ref == ref].set_index("fold").reindex(folds)["ss"].to_numpy()
        ax.bar(x + (i - (len(refs) - 1) / 2) * width, s, width, label=labels.get(ref, ref))
        if ref in sk.index:
            ax.axhline(sk.loc[ref, "ss_point"], ls=":", lw=0.8, color=f"C{i}")
    ax.axhline(0.0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"fold {f}" for f in folds])
    ax.set_ylabel("Per-fold skill score")
    ax.set_title(f"Paired per-fold skill of HANFIS vs each baseline ({tag}); dotted = pooled point estimate", fontsize=9)
    ax.legend(fontsize=7, ncol=3, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    _save(fig, out / "fig_e4_skill_per_fold")


def fig_pred_vs_true(pred: pd.DataFrame, out: Path, tag: str) -> None:
    d = pred.dropna(subset=["y_true", "y_hanfis"])
    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    for fold, g in d.groupby("fold", sort=True):
        ax.scatter(g["y_true"], g["y_hanfis"], s=9, alpha=0.55, label=f"fold {int(fold)} (n={len(g)})", linewidths=0)
    lo = float(min(d["y_true"].min(), d["y_hanfis"].min()))
    hi = float(max(d["y_true"].max(), d["y_hanfis"].max()))
    pad = 0.03 * (hi - lo if hi > lo else 1.0)
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color="black", lw=0.8, ls="--")
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlabel("Label y (realised exploitability exposure, §3.3)")
    ax.set_ylabel("HANFIS held-out prediction")
    rmse = float(np.sqrt(np.mean((d["y_true"] - d["y_hanfis"]) ** 2)))
    ax.set_title(f"Held-out prediction vs label ({tag}); RMSE={rmse:.3f}, n={len(d)}", fontsize=9)
    ax.legend(fontsize=7, frameon=False)
    ax.set_aspect("equal", adjustable="box")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    _save(fig, out / "fig_e4_pred_vs_true")


def _save(fig, stem: Path) -> None:
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--results-dir", type=Path, default=Path("results_python/e4"))
    p.add_argument("--skill-scores", type=Path, default=None, help="explicit E4_skill_scores_<ts>.csv (default: latest in --results-dir)")
    p.add_argument("--predictions", type=Path, default=None, help="explicit predictions_<ts>.csv (default: latest in --results-dir)")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--tag", default="E4", help="label printed in titles and the provenance json, e.g. e4bis")
    a = p.parse_args(argv)
    try:
        skill, pred, sp, pp = load_inputs(a.results_dir, a.skill_scores, a.predictions)
        pf = per_fold_skill(pred)
        a.out_dir.mkdir(parents=True, exist_ok=True)
        fig_forest(skill, a.out_dir, a.tag)
        fig_per_fold(pf, skill, a.out_dir, a.tag)
        fig_pred_vs_true(pred, a.out_dir, a.tag)
        pf.to_csv(a.out_dir / "e4_per_fold_skill.csv", index=False)
        prov = {
            "tag": a.tag,
            "skill_scores": str(sp),
            "predictions": str(pp),
            "n_pred_rows": int(len(pred)),
            "n_labelled": int(pred["y_true"].notna().sum()),
            "folds": sorted(int(f) for f in pred["fold"].unique()),
            "figures": ["fig_e4_skill_forest", "fig_e4_skill_per_fold", "fig_e4_pred_vs_true"],
        }
        (a.out_dir / "e4_figures_provenance.json").write_text(json.dumps(prov, indent=2))
    except FigureInputError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"wrote 3 figures (pdf+png), e4_per_fold_skill.csv, e4_figures_provenance.json -> {a.out_dir}")
    print(f"inputs: {sp.name}, {pp.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
