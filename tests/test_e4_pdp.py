"""Tests for scripts/e4_pdp.py.

These tests NEVER import torch or python_hanfis.hanfis_end2end -- they monkeypatch
make_real_backend() with a deterministic fake "model" (a plain dict of linear
coefficients) so the grid construction, fold/meta/table validation, fail-closed paths,
and output wiring can be verified without the private repo's model code or a GPU/CPU
torch install. The one thing these tests CANNOT verify is that the real HANFIS
construction in make_real_backend() matches scripts/e4_run.py's training construction;
that is caught at runtime by load_state_dict(..., strict=True) in the real repo, and
must be exercised once there (see the smoke-run instructions in the patch message).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "e4_pdp.py"
INPUTS = ["cvss", "exploitability", "patch_risk", "mfa_risk", "kubernetes_exposure",
          "asset_criticality", "threat_intelligence"]


def _load():
    spec = importlib.util.spec_from_file_location("e4_pdp", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["e4_pdp"] = mod
    spec.loader.exec_module(mod)
    return mod


def _fake_normalise(df: pd.DataFrame) -> np.ndarray:
    return df[INPUTS].to_numpy(dtype=np.float64)


def _fake_load_model(path: Path):
    # "model" is just the coefficient vector baked into the filename-derived seed,
    # so different seeds give visibly different (but deterministic) curves.
    seed = int(str(path.stem).split("seed")[1].split("_")[0])
    rng = np.random.default_rng(seed)
    return rng.normal(0, 1, size=len(INPUTS))


def _fake_predict(model, X: np.ndarray) -> np.ndarray:
    return (X @ model) / 100.0  # scaled so * 100.0 in predict_with_saved_model round-trips


def _write_table(d: Path, n=200):
    rng = np.random.default_rng(1)
    data = {
        "cvss": rng.uniform(0, 10, n), "exploitability": rng.uniform(0, 1, n),
        "patch_risk": rng.uniform(0, 2, n), "mfa_risk": rng.uniform(0, 1, n),
        "kubernetes_exposure": rng.uniform(0, 1, n),
        "asset_criticality": rng.integers(1, 6, n).astype(float),
        "threat_intelligence": rng.integers(0, 2, n).astype(float),
    }
    pd.DataFrame(data).to_csv(d / "table.csv", index=False)
    return d / "table.csv"


def _write_meta(d: Path, folds_seeds):
    saved = [{"fold": f, "seed": s, "best_val_mse": 0.001, "file": f"fold{f}_seed{s}_hanfis.pt"}
              for f, s in folds_seeds]
    meta = {"seeds": sorted({s for _, s in folds_seeds}), "saved_models": saved}
    p = d / "meta.json"
    p.write_text(json.dumps(meta))
    for f, s in folds_seeds:
        (d / f"fold{f}_seed{s}_hanfis.pt").write_bytes(b"not a real checkpoint, just needs to exist")
    return p


def test_success_path_with_mocked_backend(tmp_path, monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "make_real_backend",
                         lambda: (_fake_normalise, _fake_load_model, _fake_predict, INPUTS))
    models_dir = tmp_path / "models"; models_dir.mkdir()
    meta_path = _write_meta(models_dir, [(0, 1), (0, 2), (1, 1)])
    table = _write_table(tmp_path)
    out = tmp_path / "figs"

    rc = mod.main(["--models-dir", str(models_dir), "--meta", str(meta_path), "--table", str(table),
                   "--fold", "0", "--out-dir", str(out)])
    assert rc == 0
    for stem in ("fig_e4_pdp_one_at_a_time", "fig_e4_pdp_surface"):
        assert (out / f"{stem}.pdf").stat().st_size > 500
        assert (out / f"{stem}.png").stat().st_size > 500
    prov = json.loads((out / "e4_pdp_provenance.json").read_text())
    assert prov["fold"] == 0
    assert sorted(prov["seeds_used"]) == [1, 2]
    assert prov["pair"] == list(mod.PAIR_DEFAULT)
    assert "no premise or consequent arithmetic was reconstructed" in prov["note"]


def test_defaults_to_lowest_fold(tmp_path, monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "make_real_backend",
                         lambda: (_fake_normalise, _fake_load_model, _fake_predict, INPUTS))
    models_dir = tmp_path / "models"; models_dir.mkdir()
    meta_path = _write_meta(models_dir, [(2, 1), (3, 1)])
    table = _write_table(tmp_path)
    rc = mod.main(["--models-dir", str(models_dir), "--meta", str(meta_path), "--table", str(table),
                   "--out-dir", str(tmp_path / "o")])
    assert rc == 0
    prov = json.loads((tmp_path / "o" / "e4_pdp_provenance.json").read_text())
    assert prov["fold"] == 2


def test_one_at_a_time_curve_matches_linear_model_exactly(tmp_path, monkeypatch):
    """With the fake linear backend, sweeping input j while holding others at the median
    must trace out the EXACT line y = 100*(coef_j * x_j + sum_other coef_i * median_i)."""
    mod = _load()
    monkeypatch.setattr(mod, "make_real_backend",
                         lambda: (_fake_normalise, _fake_load_model, _fake_predict, INPUTS))
    models_dir = tmp_path / "models"; models_dir.mkdir()
    meta_path = _write_meta(models_dir, [(0, 7)])
    table = _write_table(tmp_path)
    meta = mod.load_meta(meta_path)
    fold, rows = mod.select_fold_models(meta, 0)
    stats = mod.load_table_stats(table, INPUTS)
    model_paths = [models_dir / r["file"] for r in rows]
    curves = mod.one_at_a_time(stats, INPUTS, model_paths, _fake_normalise, _fake_load_model, _fake_predict, n_points=5)

    coef = _fake_load_model(model_paths[0])
    j = INPUTS.index("cvss")
    medians = np.array([stats.loc["median", c] for c in INPUTS])
    expected = []
    for x in curves["cvss"]["x"]:
        row = medians.copy(); row[j] = x
        expected.append(float(row @ coef))
    np.testing.assert_allclose(curves["cvss"]["mean"].to_numpy(), np.array(expected), rtol=1e-10)


def test_missing_meta_fails_closed(tmp_path):
    mod = _load()
    rc = mod.main(["--models-dir", str(tmp_path), "--meta", str(tmp_path / "nope.json"),
                   "--table", str(tmp_path / "t.csv"), "--out-dir", str(tmp_path / "o")])
    assert rc == 2
    assert not (tmp_path / "o").exists()


def test_no_saved_models_fails_closed(tmp_path, capsys):
    mod = _load()
    (tmp_path / "meta.json").write_text(json.dumps({"seeds": [1], "saved_models": []}))
    rc = mod.main(["--models-dir", str(tmp_path), "--meta", str(tmp_path / "meta.json"),
                   "--table", str(tmp_path / "t.csv"), "--out-dir", str(tmp_path / "o")])
    assert rc == 2
    assert "no saved_models" in capsys.readouterr().err


def test_bad_fold_fails_closed(tmp_path):
    mod = _load()
    models_dir = tmp_path / "models"; models_dir.mkdir()
    meta_path = _write_meta(models_dir, [(0, 1)])
    rc = mod.main(["--models-dir", str(models_dir), "--meta", str(meta_path),
                   "--table", str(tmp_path / "t.csv"), "--fold", "9", "--out-dir", str(tmp_path / "o")])
    assert rc == 2


def test_missing_model_file_fails_closed(tmp_path):
    mod = _load()
    models_dir = tmp_path / "models"; models_dir.mkdir()
    meta = {"seeds": [1], "saved_models": [{"fold": 0, "seed": 1, "best_val_mse": 0.1, "file": "fold0_seed1_hanfis.pt"}]}
    meta_path = models_dir / "meta.json"; meta_path.write_text(json.dumps(meta))
    # deliberately do NOT create the .pt file
    rc = mod.main(["--models-dir", str(models_dir), "--meta", str(meta_path),
                   "--table", str(tmp_path / "t.csv"), "--out-dir", str(tmp_path / "o")])
    assert rc == 2


def test_missing_table_column_fails_closed(tmp_path, monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "make_real_backend",
                         lambda: (_fake_normalise, _fake_load_model, _fake_predict, INPUTS))
    models_dir = tmp_path / "models"; models_dir.mkdir()
    meta_path = _write_meta(models_dir, [(0, 1)])
    table_path = _write_table(tmp_path)
    df = pd.read_csv(table_path).drop(columns=["asset_criticality"])
    df.to_csv(table_path, index=False)
    rc = mod.main(["--models-dir", str(models_dir), "--meta", str(meta_path), "--table", str(table_path),
                   "--out-dir", str(tmp_path / "o")])
    assert rc == 2


def test_bad_pair_fails_closed(tmp_path, monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "make_real_backend",
                         lambda: (_fake_normalise, _fake_load_model, _fake_predict, INPUTS))
    models_dir = tmp_path / "models"; models_dir.mkdir()
    meta_path = _write_meta(models_dir, [(0, 1)])
    table = _write_table(tmp_path)
    rc = mod.main(["--models-dir", str(models_dir), "--meta", str(meta_path), "--table", str(table),
                   "--pair", "not_a_column", "cvss", "--out-dir", str(tmp_path / "o")])
    assert rc == 2
