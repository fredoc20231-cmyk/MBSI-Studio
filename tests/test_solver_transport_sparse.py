"""Tests for sparse top-k transport plan storage."""

import pytest

pytestmark = pytest.mark.heavy

import numpy as np

from mbsi.reconstruction.transport_sparse import (
    apply_transport_to_expression,
    compress_transport_plan,
)
from mbsi.reconstruction.solver import run_mbsi
import anndata as ad


def test_compress_transport_top_k():
    rng = np.random.default_rng(0)
    plan = rng.random((20, 100))
    sparse = compress_transport_plan(plan, top_k=10)
    assert sparse["format"] == "top_k_edges"
    assert sparse["top_k"] == 10
    assert len(sparse["weight"]) <= 20 * 10
    assert sparse["memory_sparse_bytes"] < sparse["memory_dense_bytes"]
    assert sparse["memory_savings_ratio"] > 1


def test_apply_transport_sparse_matches_dense():
    rng = np.random.default_rng(1)
    plan = rng.random((5, 12))
    plan /= plan.sum(axis=1, keepdims=True)
    expr = rng.random((5, 8))
    sparse = compress_transport_plan(plan, top_k=50)
    dense_out = plan.T @ expr
    sparse_out = apply_transport_to_expression(expr, sparse)
    np.testing.assert_allclose(dense_out, sparse_out, rtol=1e-5)


def test_run_mbsi_stores_sparse_transport():
    n_spots, n_genes = 6, 15
    adata = ad.AnnData(X=np.random.rand(n_spots, n_genes))
    adata.obsm["spatial"] = np.random.randn(n_spots, 2)
    recon = run_mbsi(adata, n_cells_per_spot=4, top_k_transport=5, max_iter=20, random_state=2)
    tp = recon.uns["transport_plan"]
    assert isinstance(tp, dict)
    assert tp["format"] == "top_k_edges"
    assert tp["top_k"] == 5
    assert "csr" in tp
    assert tp["memory_savings_ratio"] >= 1
