"""Tests for mbsi.foundation (embeddings 45%, predict 32%)."""

import anndata as ad
import numpy as np

from mbsi.foundation.embeddings import compute_tissue_embedding
from mbsi.foundation.predict import predict_missing_genes, zero_shot_annotate_regions


def _make_adata(n_obs=30, n_vars=15, seed=0):
    rng = np.random.RandomState(seed)
    adata = ad.AnnData(X=rng.rand(n_obs, n_vars).astype(np.float32))
    adata.var_names = [f"gene_{i}" for i in range(n_vars)]
    adata.obs_names = [f"cell_{i}" for i in range(n_obs)]
    return adata


# --- embeddings ---


def test_compute_tissue_embedding_shape():
    adata = _make_adata()
    emb = compute_tissue_embedding(adata, n_components=5)
    assert emb.shape == (30, 5)
    assert emb.dtype == np.float32


def test_compute_tissue_embedding_clamped_components():
    adata = _make_adata(n_obs=5, n_vars=3)
    emb = compute_tissue_embedding(adata, n_components=30)
    assert emb.shape[0] == 5
    assert emb.shape[1] <= 3


def test_compute_tissue_embedding_with_multimodal():
    adata = _make_adata(n_obs=20, n_vars=10)
    adata.obsm["multimodal_raw"] = np.random.rand(20, 5).astype(np.float32)
    emb = compute_tissue_embedding(adata, n_components=8)
    assert emb.shape == (20, 8)


# --- predict ---


def test_predict_missing_genes_adds_imputed():
    adata = _make_adata()
    result = predict_missing_genes(adata, ["NEWGENE1", "NEWGENE2"])
    assert "imputed_NEWGENE1" in result.obs.columns
    assert "imputed_NEWGENE2" in result.obs.columns
    assert "imputation_note" in result.uns


def test_predict_missing_genes_existing_skipped():
    adata = _make_adata()
    result = predict_missing_genes(adata, ["gene_0"])
    assert "imputed_gene_0" not in result.obs.columns


def test_predict_missing_genes_no_mutation():
    adata = _make_adata()
    original_obs_cols = set(adata.obs.columns)
    predict_missing_genes(adata, ["NEWGENE"])
    assert set(adata.obs.columns) == original_obs_cols


def test_zero_shot_annotate_regions():
    adata = _make_adata(n_obs=20)
    result = zero_shot_annotate_regions(adata, n_regions=3)
    assert "region_annotation" in result.obs.columns
    assert len(result.obs["region_annotation"].unique()) <= 3
    assert "annotation_note" in result.uns


def test_zero_shot_annotate_regions_more_regions_than_obs():
    adata = _make_adata(n_obs=3, n_vars=5)
    result = zero_shot_annotate_regions(adata, n_regions=10)
    assert "region_annotation" in result.obs.columns
    assert len(result.obs["region_annotation"].unique()) <= 3
