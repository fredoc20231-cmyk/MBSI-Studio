"""Bridge integration for multimodal datasets."""

from __future__ import annotations

from typing import Any, Dict, Tuple

import anndata as ad
import numpy as np
from sklearn.decomposition import PCA


def run_bridge_integration(
    adata: ad.AnnData,
    anchor_key: str = "batch",
    n_dims: int = 30,
) -> Tuple[ad.AnnData, str]:
    """Bridge integration; fallback to PCA on concatenated modalities."""
    adata = adata.copy()
    parts = []
    for key in adata.obsm.keys():
        if key.startswith("X_") and key != "X_pca":
            parts.append(adata.obsm[key])
    if not parts and "X_pca" in adata.obsm:
        return adata, "Bridge unavailable — using existing PCA"
    if not parts:
        return adata, "Bridge unavailable — no modality embeddings found"

    combined = np.hstack(parts)
    n_dims = min(n_dims, combined.shape[1], adata.n_obs - 1)
    pca = PCA(n_components=max(1, n_dims), random_state=0)
    adata.obsm["X_integrated"] = pca.fit_transform(combined)
    note = "Bridge integration via concat-PCA fallback (full Seurat bridge unavailable)"
    adata.uns["bridge"] = {"method": "concat_pca", "anchor_key": anchor_key}
    return adata, note
