"""Tests for generic h5ad and CSV ingestion."""

import tempfile
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import pytest

from mbsi.io.generic import ingest_csv_matrix_coords, ingest_h5ad, load_h5ad
from mbsi.io.validators import validate_adata_contract


def test_ingest_h5ad_contract():
    n_obs, n_vars = 12, 60
    X = np.random.poisson(3, (n_obs, n_vars)).astype(float)
    adata = ad.AnnData(X=X)
    adata.var_names = [f"g{i}" for i in range(n_vars)]
    adata.obs_names = [f"s{i}" for i in range(n_obs)]
    adata.obsm["spatial"] = np.column_stack([np.arange(n_obs), np.zeros(n_obs)]).astype(float)

    with tempfile.NamedTemporaryFile(suffix=".h5ad", delete=False) as f:
        path = Path(f.name)
    try:
        adata.write_h5ad(path)
        loaded, meta = ingest_h5ad(path)
        assert loaded.n_obs == n_obs
        assert loaded.uns["mbsi_platform"] == "generic_h5ad"
        assert meta["readiness_score"] >= 50
        contract = validate_adata_contract(loaded)
        assert contract["valid"]
    finally:
        path.unlink(missing_ok=True)


def test_load_h5ad_direct():
    adata = ad.AnnData(X=np.ones((5, 10)))
    adata.obsm["spatial"] = np.zeros((5, 2))
    with tempfile.NamedTemporaryFile(suffix=".h5ad", delete=False) as f:
        path = Path(f.name)
    try:
        adata.write_h5ad(path)
        loaded = load_h5ad(path)
        assert loaded.shape == (5, 10)
    finally:
        path.unlink(missing_ok=True)


def test_ingest_csv_matrix_coords():
    matrix = pd.DataFrame(
        np.random.poisson(2, (8, 30)),
        index=[f"spot_{i}" for i in range(8)],
        columns=[f"g{i}" for i in range(30)],
    )
    coords = pd.DataFrame({"x": np.arange(8), "y": np.arange(8) * 2}, index=matrix.index)
    loaded, meta = ingest_csv_matrix_coords(matrix, coords)
    assert loaded.n_obs == 8
    assert loaded.uns["mbsi_platform"] == "csv_matrix"
    assert "spatial" in loaded.obsm
    assert meta["readiness_score"] > 0


def test_csv_coords_requires_xy():
    matrix = pd.DataFrame(np.ones((3, 5)))
    coords = pd.DataFrame({"a": [1, 2, 3]})
    with pytest.raises(ValueError, match="x.*y"):
        ingest_csv_matrix_coords(matrix, coords)
