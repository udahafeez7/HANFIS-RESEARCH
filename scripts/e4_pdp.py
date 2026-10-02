#!/usr/bin/env python
"""Partial-dependence and surface-view figures for a saved HANFIS model (A-08).

Companion to --save-models in scripts/e4_run.py. Deliberately does NOT reconstruct the
Gaussian membership curves or Sugeno consequent arithmetic by hand from the state_dict --
guessing the sigma transform (exp vs softplus) or the consequent/bias column order would
produce a figure that *looks* right and may not be. Instead every curve/surface in this
script is the REAL model's forward pass (the same `predict` function scripts/e4_run.py
uses for the confirmatory result), evaluated on a synthetic input grid:

  - one raw input swept across its observed [p1, p99] range, the other six held at the
    training table's per-input median (one-at-a-time partial dependence, 7 panels)
  - one declared pair of raw inputs swept on a 2D grid, the rest held at median
    (surface view; default pair: kubernetes_exposure x asset_criticality)

Architecture mismatch is caught by `load_state_dict(..., strict=True)`: if the HANFIS
hyperparameters hard-coded below (m_raw=2, m_intermediate=3, mf_family="gauss",
monotone=True) ever drift from scripts/e4_run.py's training construction, loading fails
loudly instead of silently plotting a wrong model.

Usage:
  python scripts/e4_pdp.py --models-dir results_python/e4bis_120/models \
      --meta results_python/e4bis_120/meta_<ts>.json \
      --table data/processed/asset_weeks_v2_120assets_e4bis.csv \
      --fold 0 --out-dir manuscript/figures/e4bis_pdp

By default all seeds saved for the chosen fold are overlaid (thin lines) with their mean
highlighted, so seed-to-seed instability is visible rather than hidden behind one cherry-
picked seed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

PAIR_DEFAULT = ("kubernetes_exposure", "asset_criticality")


class PDPInputError(RuntimeError):
    pass


def load_meta(meta_path: Path) -> dict:
    if not meta_path.is_file():
        raise PDPInputError(f"meta file not found: {meta_path}")
    meta = json.loads(meta_path.read_text())
    if not meta.get("saved_models"):
        raise PDPInputError(
            f"{meta_path} has no saved_models -- this run was not launched with --save-models "
            "(scripts/e4_run.py), or it finished training zero HANFIS seeds."
        )
    return meta


def select_fold_models(meta: dict, fold: int | None) -> tuple[int, list[dict]]:
    saved = meta["saved_models"]
    folds = sorted({r["fold"] for r in saved})
    if fold is None:
        fold = folds[0]
    if fold not in folds:
        raise PDPInputError(f"fold {fold} not in saved folds {folds}")
    rows = [r for r in saved if r["fold"] == fold]
    return fold, rows


def load_table_stats(table_path: Path, inputs: list[str]) -> pd.DataFrame:
    if not table_path.is_file():
        raise PDPInputError(f"table not found: {table_path}")
    df = pd.read_csv(table_path, low_memory=False)
    missing = [c for c in inputs if c not in df.columns]
    if missing:
        raise PDPInputError(f"{table_path}: missing input columns {missing}")
    stats = df[inputs].agg(["median", lambda s: s.quantile(0.01), lambda s: s.quantile(0.99)])
    stats.index = ["median", "p01", "p99"]
    if stats.isna().any().any():
        bad = stats.columns[stats.isna().any()].tolist()
        raise PDPInputError(f"{table_path}: all-NaN or insufficient data for input(s) {bad}")
    return stats


def build_grid_rows(stats: pd.DataFrame, inputs: list[str], sweep: str, values: np.ndarray) -> pd.DataFrame:
    base = {c: float(stats.loc["median", c]) for c in inputs}
    rows = [dict(base, **{sweep: float(v)}) for v in values]
    return pd.DataFrame(rows, columns=inputs)


def build_grid_rows_pair(stats: pd.DataFrame, inputs: list[str], sx: str, sy: str,
                          vx: np.ndarray, vy: np.ndarray) -> pd.DataFrame:
    base = {c: float(stats.loc["median", c]) for c in inputs}
    gx, gy = np.meshgrid(vx, vy)
    rows = []
    for x, y in zip(gx.ravel(), gy.ravel()):
        rows.append(dict(base, **{sx: float(x), sy: float(y)}))
    return pd.DataFrame(rows, columns=inputs)


def predict_with_saved_model(model_path: Path, X_raw: pd.DataFrame,
                              normalise_fn: Callable[[pd.DataFrame], np.ndarray],
                              load_model_fn: Callable[[Path], object],
                              predict_fn: Callable[[object, np.ndarray], np.ndarray]) -> np.ndarray:
    """normalise_fn/load_model_fn/predict_fn are injected so this logic is unit-testable
    without torch or the private hanfis_end2end module installed."""
    model = load_model_fn(model_path)
    X = normalise_fn(X_raw)
    return predict_fn(model, X) * 100.0


def _real_normalise(e4_run_module):
    return e4_run_module.normalise


def _real_load_model(e4_run_module, hanfis_module, torch_module):
    def _load(path: Path):
        model = hanfis_module.HANFIS(m_raw=2, m_intermediate=3, mf_family="gauss", monotone=True)
        state = torch_module.load(path, map_location="cpu")
        model.load_state_dict(state, strict=True)
        model.eval()
        return model
    return _load


def _real_predict(hanfis_module):
    return hanfis_module.predict


def make_real_backend():
    """Import the project's actual code. Raises PDPInputError with a clear message if the
    repo layout / dependencies are not as expected, rather than an opaque ImportError."""
    try:
        sys.path.insert(0, str(ROOT / "python_hanfis"))
        import torch  # noqa: WPS433
        import hanfis_end2end as hanfis_module  # noqa: WPS433
        sys.path.insert(0, str(ROOT / "scripts"))
        import e4_run as e4_run_module  # noqa: WPS433
    except Exception as exc:  # pragma: no cover -- exercised only without the private repo
        raise PDPInputError(
            "could not import torch / python_hanfis.hanfis_end2end / scripts.e4_run -- "
            f"run this from the repo root with the anfis venv active ({exc})"
        ) from exc
    return (
        _real_normalise(e4_run_module),
        _real_load_model(e4_run_module, hanfis_module, torch),
        _real_predict(hanfis_module),
        e4_run_module.INPUTS,
    )


def one_at_a_time(stats: pd.DataFrame, inputs: list[str], model_paths: list[Path],
                   normalise_fn, load_model_fn, predict_fn, n_points: int = 60) -> dict[str, pd.DataFrame]:
    curves = {}
    for inp in inputs:
        values = np.linspace(float(stats.loc["p01", inp]), float(stats.loc["p99", inp]), n_points)
        grid = build_grid_rows(stats, inputs, inp, values)
        preds = []
        for mp in model_paths:
            preds.append(predict_with_saved_model(mp, grid, normalise_fn, load_model_fn, predict_fn))
        arr = np.asarray(preds)  # (n_models, n_points)
        curves[inp] = pd.DataFrame({"x": values, "mean": arr.mean(axis=0),
                                     **{f"seed_{i}": arr[i] for i in range(arr.shape[0])}})
    return curves


def pair_surface(stats: pd.DataFrame, inputs: list[str], sx: str, sy: str, model_paths: list[Path],
                  normalise_fn, load_model_fn, predict_fn, n_points: int = 30) -> dict:
    vx = np.linspace(float(stats.loc["p01", sx]), float(stats.loc["p99", sx]), n_points)
    vy = np.linspace(float(stats.loc["p01", sy]), float(stats.loc["p99", sy]), n_points)
    grid = build_grid_rows_pair(stats, inputs, sx, sy, vx, vy)
    preds = []
    for mp in model_paths:
        preds.append(predict_with_saved_model(mp, grid, normalise_fn, load_model_fn, predict_fn))
    mean = np.mean(preds, axis=0).reshape(n_points, n_points)
    return {"vx": vx, "vy": vy, "z": mean}


def plot_one_at_a_time(curves: dict[str, pd.DataFrame], out_dir: Path, tag: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    inputs = list(curves.keys())
    ncols = 4
    nrows = -(-len(inputs) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.2 * ncols, 2.6 * nrows), squeeze=False)
    for ax, inp in zip(axes.flat, inputs):
        df = curves[inp]
        seed_cols = [c for c in df.columns if c.startswith("seed_")]
        for c in seed_cols:
            ax.plot(df["x"], df[c], color="#9ecae1", lw=0.8, alpha=0.8)
        ax.plot(df["x"], df["mean"], color="#08519c", lw=2.0)
        ax.set_title(inp, fontsize=9)
        ax.set_xlabel("raw value", fontsize=7.5)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    for ax in axes.flat[len(inputs):]:
        ax.axis("off")
    fig.suptitle(f"HANFIS partial dependence, one raw input at a time, others at sample median ({tag})", fontsize=10)
    fig.supylabel("Predicted y (0-100 scale)", fontsize=8.5)
    fig.tight_layout(rect=(0.02, 0, 1, 0.95))
    fig.savefig(out_dir / "fig_e4_pdp_one_at_a_time.pdf", bbox_inches="tight")
    fig.savefig(out_dir / "fig_e4_pdp_one_at_a_time.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_pair_surface(surf: dict, sx: str, sy: str, out_dir: Path, tag: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.0, 4.2))
    cs = ax.contourf(surf["vx"], surf["vy"], surf["z"], levels=20, cmap="viridis")
    fig.colorbar(cs, ax=ax, label="Predicted y (0-100 scale)")
    ax.set_xlabel(sx); ax.set_ylabel(sy)
    ax.set_title(f"Surface view (A-08): {sx} x {sy}, others at sample median ({tag})", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "fig_e4_pdp_surface.pdf", bbox_inches="tight")
    fig.savefig(out_dir / "fig_e4_pdp_surface.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--models-dir", type=Path, required=True)
    p.add_argument("--meta", type=Path, required=True)
    p.add_argument("--table", type=Path, required=True)
    p.add_argument("--fold", type=int, default=None, help="default: lowest fold index with saved models")
    p.add_argument("--pair", nargs=2, default=list(PAIR_DEFAULT), metavar=("X", "Y"))
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--tag", default="E4-bis")
    a = p.parse_args(argv)
    try:
        meta = load_meta(a.meta)
        fold, rows = select_fold_models(meta, a.fold)
        model_paths = [a.models_dir / r["file"] for r in rows]
        for mp in model_paths:
            if not mp.is_file():
                raise PDPInputError(f"model file listed in meta but not found on disk: {mp}")

        normalise_fn, load_model_fn, predict_fn, inputs = make_real_backend()
        stats = load_table_stats(a.table, inputs)

        sx, sy = a.pair
        if sx not in inputs or sy not in inputs:
            raise PDPInputError(f"--pair must be two of {inputs}, got {a.pair}")

        a.out_dir.mkdir(parents=True, exist_ok=True)
        curves = one_at_a_time(stats, inputs, model_paths, normalise_fn, load_model_fn, predict_fn)
        plot_one_at_a_time(curves, a.out_dir, a.tag)
        surf = pair_surface(stats, inputs, sx, sy, model_paths, normalise_fn, load_model_fn, predict_fn)
        plot_pair_surface(surf, sx, sy, a.out_dir, a.tag)

        prov = {
            "tag": a.tag, "fold": fold, "seeds_used": [r["seed"] for r in rows],
            "model_files": [str(mp) for mp in model_paths], "meta": str(a.meta), "table": str(a.table),
            "pair": [sx, sy], "sample_medians": {c: float(stats.loc["median", c]) for c in inputs},
            "note": "all curves/surface are the real model's forward pass (hanfis_predict); "
                    "no premise or consequent arithmetic was reconstructed by hand.",
        }
        (a.out_dir / "e4_pdp_provenance.json").write_text(json.dumps(prov, indent=2))
    except PDPInputError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    print(f"wrote fig_e4_pdp_one_at_a_time.{{pdf,png}}, fig_e4_pdp_surface.{{pdf,png}}, "
          f"e4_pdp_provenance.json -> {a.out_dir}")
    print(f"fold {fold}, seeds {[r['seed'] for r in rows]}, pair {sx} x {sy}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
