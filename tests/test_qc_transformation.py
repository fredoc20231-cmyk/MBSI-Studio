"""Tests for QC & Transformation backend and workspace."""

import numpy as np
import pandas as pd
import anndata as ad


def _mini_adata(n=40, g=50):
    X = np.random.poisson(5, (n, g)).astype(float)
    obs = pd.DataFrame({
        "sample_id": ["S1"] * (n // 2) + ["S2"] * (n - n // 2),
        "condition": ["A"] * (n // 2) + ["B"] * (n - n // 2),
        "total_counts": X.sum(axis=1),
        "n_genes_by_counts": (X > 0).sum(axis=1),
        "pct_counts_mt": np.random.uniform(1, 10, n),
        "in_tissue": np.ones(n, dtype=bool),
    })
    var = pd.DataFrame(index=[f"G{i}" for i in range(g)])
    adata = ad.AnnData(X, obs=obs, var=var)
    adata.obsm["spatial"] = np.column_stack([np.random.rand(n), np.random.rand(n)])
    return adata


def test_qc_summary():
    from mbsi.qc import compute_original_summary

    adata = _mini_adata()
    summary = compute_original_summary(adata)
    assert not summary.empty
    assert "counts_mean" in summary.columns


def test_filter_data():
    from mbsi.qc import filter_data

    adata = _mini_adata()
    adata.obs["qc_pass"] = True
    filtered, _, warnings = filter_data(adata, min_counts=0, min_genes=0, max_mito_pct=100)
    assert filtered.n_obs <= adata.n_obs


def test_normalize():
    from mbsi.preprocessing import normalize

    adata = _mini_adata()
    out, note = normalize(adata, method="log")
    assert out.n_obs == adata.n_obs
    assert "log" in note.lower()


def test_qc_transformation_workspace_import():
    import importlib

    mod = importlib.import_module("app.workspaces.qc_transformation")
    assert callable(mod.render)
