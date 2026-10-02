"""Tests for scripts/e4_figures.py: success path on synthetic E4-shaped CSVs
and fail-closed behaviour on missing inputs / missing columns / empty tables."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "e4_figures.py"


def _load():
    spec = importlib.util.spec_from_file_location("e4_figures", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["e4_figures"] = mod
    spec.loader.exec_module(mod)
    return mod


SKILL_HEADER = "ref,hypothesis,ss_point,ci_lo,ci_hi,sesoi_or_margin,p_boot_at_margin,n_boot_valid,p_holm,confirmed"
PRED_HEADER = "event_id,image_id,fold,y_true,y_hanfis,y_cvss_only,y_persistence,y_ridge_7inputs,y_matched,y_flat_full"


def _write_inputs(d: Path, ts="20261001T041031Z", n_folds=5, n_per_fold=40, with_nan=True):
    rng = np.random.default_rng(0)
    rows = []
    for f in range(n_folds):
        for i in range(n_per_fold):
            y = float(rng.uniform(0, 10))
            rows.append({
                "event_id": f"img{f}_{i}__2026-W{10 + i:02d}",
                "image_id": f"docker.io/x/img{f}@sha256:{'0' * 64}",
                "fold": f,
                "y_true": y if not (with_nan and i % 13 == 0) else np.nan,
                "y_hanfis": y + rng.normal(0, 0.5),
                "y_cvss_only": rng.uniform(0, 10),
                "y_persistence": y + rng.normal(0, 0.9),
                "y_ridge_7inputs": y + rng.normal(0, 0.7),
                "y_matched": y + rng.normal(0, 0.6),
                "y_flat_full": y + rng.normal(0, 0.8),
            })
    pred = pd.DataFrame(rows)
    assert list(pred.columns) == PRED_HEADER.split(",")
    pred.to_csv(d / f"predictions_{ts}.csv", index=False)
    skill = pd.DataFrame([
        ["cvss_only", "H1a", 0.9688, 0.9393, 0.9899, 0.1, 0.0, 2000.0, 0.0, True],
        ["ridge_7inputs", "H1c", 0.7150, 0.5181, 0.8926, 0.0, 0.0, 2000.0, 0.0, True],
        ["matched", "H2", 0.8163, 0.6493, 0.9333, 0.0, 0.0, 2000.0, 0.0, True],
        ["persistence", "H1b", 0.3001, -0.0351, 0.4167, 0.0, 0.05, 2000.0, 0.0415, False],
    ], columns=SKILL_HEADER.split(","))
    skill.to_csv(d / f"E4_skill_scores_{ts}.csv", index=False)
    return pred, skill


def test_success_path_writes_all_outputs(tmp_path):
    mod = _load()
    res = tmp_path / "res"; res.mkdir()
    _write_inputs(res)
    # an OLDER pair must be ignored in favour of the latest timestamp
    _write_inputs(res, ts="20260901T000000Z", n_folds=2, n_per_fold=5)
    out = tmp_path / "figs"
    rc = mod.main(["--results-dir", str(res), "--out-dir", str(out), "--tag", "e4test"])
    assert rc == 0
    for stem in ("fig_e4_skill_forest", "fig_e4_skill_per_fold", "fig_e4_pred_vs_true"):
        assert (out / f"{stem}.pdf").stat().st_size > 1000
        assert (out / f"{stem}.png").stat().st_size > 1000
    prov = json.loads((out / "e4_figures_provenance.json").read_text())
    assert prov["tag"] == "e4test"
    assert prov["predictions"].endswith("predictions_20261001T041031Z.csv")
    assert prov["folds"] == [0, 1, 2, 3, 4]
    pf = pd.read_csv(out / "e4_per_fold_skill.csv")
    assert set(pf["ref"]) == {"persistence", "cvss_only", "ridge_7inputs", "matched", "flat_full"}
    assert len(pf) == 5 * 5
    # HANFIS noise sd 0.5 vs cvss_only uniform noise / persistence sd 0.9 -> clearly positive
    assert (pf[pf.ref.isin(["cvss_only", "persistence"])]["ss"] > 0).all()
    assert pf["ss"].notna().all()


def test_per_fold_skill_matches_manual(tmp_path):
    mod = _load()
    pred, _ = _write_inputs(tmp_path, with_nan=False)
    pf = mod.per_fold_skill(pred).set_index(["fold", "ref"])
    g = pred[pred.fold == 2]
    mse_h = np.mean((g.y_true - g.y_hanfis) ** 2)
    mse_p = np.mean((g.y_true - g.y_persistence) ** 2)
    assert pf.loc[(2, "persistence"), "ss"] == pytest.approx(1 - mse_h / mse_p)


def test_missing_results_dir_fails_closed(tmp_path, capsys):
    mod = _load()
    rc = mod.main(["--results-dir", str(tmp_path / "nope"), "--out-dir", str(tmp_path / "o")])
    assert rc == 2
    assert "no E4_skill_scores_<timestamp>.csv" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


def test_missing_column_fails_closed(tmp_path, capsys):
    mod = _load()
    res = tmp_path / "res"; res.mkdir()
    pred, _ = _write_inputs(res)
    pred.drop(columns=["y_matched"]).to_csv(res / "predictions_20261001T041031Z.csv", index=False)
    rc = mod.main(["--results-dir", str(res), "--out-dir", str(tmp_path / "o")])
    assert rc == 2
    assert "missing columns ['y_matched']" in capsys.readouterr().err


def test_empty_table_fails_closed(tmp_path, capsys):
    mod = _load()
    res = tmp_path / "res"; res.mkdir()
    _write_inputs(res)
    (res / "E4_skill_scores_20261001T041031Z.csv").write_text(SKILL_HEADER + "\n")
    rc = mod.main(["--results-dir", str(res), "--out-dir", str(tmp_path / "o")])
    assert rc == 2
    assert "has no rows" in capsys.readouterr().err


def test_explicit_paths_override_latest(tmp_path):
    mod = _load()
    res = tmp_path / "res"; res.mkdir()
    _write_inputs(res, ts="20260901T000000Z")
    _write_inputs(res, ts="20261001T041031Z")
    out = tmp_path / "o"
    rc = mod.main(["--results-dir", str(res), "--out-dir", str(out),
                   "--predictions", str(res / "predictions_20260901T000000Z.csv")])
    assert rc == 0
    prov = json.loads((out / "e4_figures_provenance.json").read_text())
    assert prov["predictions"].endswith("20260901T000000Z.csv")
    assert prov["skill_scores"].endswith("20261001T041031Z.csv")
