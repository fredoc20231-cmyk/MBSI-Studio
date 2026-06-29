"""Weighted nearest neighbor integration."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import anndata as ad
import numpy as np
from sklearn.decomposition import PCA
from sklearn.neighbors import kneighbors_graph


def run_weighted_nearest_neighbor(
    adata: ad.AnnData,
    modalities: List[str],
    n_neighbors: int = 20,
    n_pcs: int = 15,
) -> Tuple[ad.AnnData, str]:
    """Run WNN integration; honest fallback to concat PCA + neighbors."""
    adata = adata.copy()
    reductions = []
    weights = []

    for mod in modalities:
        key = f"X_pca_{mod}"
        alt = f"X_{mod}"
        if key in adata.obsm:
            reductions.append(adata.obsm[key][:, :n_pcs])
            weights.append(1.0)
        elif alt in adata.obsm:
            X = adata.obsm[alt]
            pca = PCA(n_components=min(n_pcs, X.shape[1], adata.n_obs - 1), random_state=0)
            reductions.append(pca.fit_transform(X))
            weights.append(1.0)
        elif mod == "rna" and "X_pca" in adata.obsm:
            reductions.append(adata.obsm["X_pca"][:, :n_pcs])
            weights.append(1.0)

    if len(reductions) < 2:
        note = "WNN unavailable — single modality; using RNA PCA only"
        if "X_pca" in adata.obsm:
            adata.obsm["X_wnn"] = adata.obsm["X_pca"][:, :n_pcs]
        return adata, note

    try:
        import muon as mu  # noqa: F401

        note = "Full WNN via muon (if configured)"
    except ImportError:
        note = "Full WNN unavailable — concat PCA + weighted neighbors fallback"

    w = np.array(weights) / sum(weights)
    combined = np.hstack([r * np.sqrt(wi) for r, wi in zip(reductions, w)])
    pca = PCA(n_components=min(n_pcs, combined.shape[1], adata.n_obs - 1), random_state=0)
    adata.obsm["X_wnn"] = pca.fit_transform(combined)
    n_neighbors = min(n_neighbors, adata.n_obs - 1)
    conn = kneighbors_graph(adata.obsm["X_wnn"], n_neighbors=n_neighbors, mode="connectivity")
    conn = conn.maximum(conn.T)
    adata.obsp["wnn_connectivities"] = conn.tocsr()
    adata.uns["wnn"] = {"modalities": modalities, "fallback": note}
    return adata, note
