"""Tests for mbsi.reconstruction.postprocess module (11% -> target ~80%)."""

import os
import tempfile

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.reconstruction.postprocess import (
    compute_gene_statistics,
    export_to_csv,
    postprocess_reconstruction,
)


def _make_adata(n_obs=50, n_vars=20, seed=42):
    rng = np.random.RandomState(seed)
    X = rng.rand(n_obs, n_vars).astype(np.float32) * 100
    adata = ad.AnnData(X=X)
    adata.var_names = [f"gene_{i}" for i in range(n_vars)]
    adata.obs_names = [f"cell_{i}" for i in range(n_obs)]
    adata.obsm["spatial"] = rng.rand(n_obs, 2).astype(np.float32) * 100
    return adata


def test_postprocess_defaults():
    adata = _make_adata()
    result = postprocess_reconstruction(adata)
    assert isinstance(result, ad.AnnData)
    assert result.n_obs <= adata.n_obs
    assert result.n_vars <= adata.n_vars


def test_postprocess_no_normalize():
    adata = _make_adata()
    result = postprocess_reconstruction(adata, normalize=False)
    assert isinstance(result, ad.AnnData)


def test_postprocess_no_log_transform():
    adata = _make_adata()
    result = postprocess_reconstruction(adata, log_transform=False)
    assert isinstance(result, ad.AnnData)


def test_postprocess_no_filter():
    adata = _make_adata()
    result = postprocess_reconstruction(adata, filter_genes=False)
    assert result.n_obs == adata.n_obs
    assert result.n_vars == adata.n_vars


def test_postprocess_all_disabled():
    adata = _make_adata()
    result = postprocess_reconstruction(
        adata, normalize=False, log_transform=False, filter_genes=False
    )
    assert result.n_obs == adata.n_obs
    assert result.n_vars == adata.n_vars


def test_compute_gene_statistics():
    adata = _make_adata()
    result = compute_gene_statistics(adata)
    assert "mean_expression" in result.var.columns
    assert "std_expression" in result.var.columns
    assert "n_cells_expressing" in result.var.columns
    assert "fraction_expressing" in result.var.columns
    assert len(result.var["mean_expression"]) == adata.n_vars
    assert (result.var["fraction_expressing"] >= 0).all()
    assert (result.var["fraction_expressing"] <= 1).all()


def test_export_to_csv():
    adata = _make_adata()
    adata.obs["cell_type"] = "epithelial"
    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = os.path.join(tmpdir, "output")
        export_to_csv(adata, prefix)
        assert os.path.exists(f"{prefix}_expression.csv")
        assert os.path.exists(f"{prefix}_coordinates.csv")
        assert os.path.exists(f"{prefix}_metadata.csv")

        expr = pd.read_csv(f"{prefix}_expression.csv", index_col=0)
        assert expr.shape == (adata.n_obs, adata.n_vars)

        coords = pd.read_csv(f"{prefix}_coordinates.csv", index_col=0)
        assert set(coords.columns) == {"x", "y"}
        assert len(coords) == adata.n_obs


def test_export_to_csv_no_cell_type():
    adata = _make_adata()
    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = os.path.join(tmpdir, "output")
        export_to_csv(adata, prefix)
        assert os.path.exists(f"{prefix}_expression.csv")
        assert os.path.exists(f"{prefix}_coordinates.csv")
        assert not os.path.exists(f"{prefix}_metadata.csv")
