"""Tests for mbsi.temporal.dynamics module (24% -> target ~90%)."""

import anndata as ad
import numpy as np

from mbsi.temporal.dynamics import estimate_spatial_dynamics


def _make_adata(n_obs=20, n_vars=10, seed=0):
    rng = np.random.RandomState(seed)
    adata = ad.AnnData(X=rng.rand(n_obs, n_vars).astype(np.float32))
    adata.var_names = [f"gene_{i}" for i in range(n_vars)]
    adata.obs_names = [f"cell_{i}" for i in range(n_obs)]
    return adata


def test_single_timepoint():
    result = estimate_spatial_dynamics([_make_adata()])
    assert result["transitions"] == []
    assert "Need" in result["note"]


def test_two_timepoints():
    t0 = _make_adata(seed=0)
    t1 = _make_adata(seed=1)
    result = estimate_spatial_dynamics([t0, t1])
    assert len(result["transitions"]) == 1
    tr = result["transitions"][0]
    assert tr["from"] == 0
    assert tr["to"] == 1
    assert "mean_expression_change" in tr


def test_three_timepoints():
    adatas = [_make_adata(seed=i) for i in range(3)]
    result = estimate_spatial_dynamics(adatas)
    assert len(result["transitions"]) == 2


def test_immune_fraction_with_compartment():
    t0 = _make_adata(seed=0)
    t1 = _make_adata(seed=1)
    t1.obs["compartment"] = ["immune"] * 10 + ["tumor"] * 10
    result = estimate_spatial_dynamics([t0, t1])
    assert result["transitions"][0]["immune_fraction"] == 0.5


def test_immune_fraction_without_compartment():
    t0 = _make_adata(seed=0)
    t1 = _make_adata(seed=1)
    result = estimate_spatial_dynamics([t0, t1])
    assert result["transitions"][0]["immune_fraction"] == 0.0
