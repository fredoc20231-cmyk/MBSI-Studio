"""Tissue embeddings (foundation-ready, lightweight)."""

import anndata as ad
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from mbsi.utils import to_dense_array


def compute_tissue_embedding(adata: ad.AnnData, n_components: int = 30) -> np.ndarray:
    """
    Compute tissue embedding via PCA (foundation-ready module).

    Not a trained foundation model — placeholder for future upgrade.
    """
    X = to_dense_array(adata.X)
    if "multimodal_raw" in adata.obsm:
        X = np.hstack([X, adata.obsm["multimodal_raw"]])
    n_components = min(n_components, X.shape[0], X.shape[1])
    emb = PCA(n_components=n_components, random_state=42).fit_transform(StandardScaler().fit_transform(X))
    return emb.astype(np.float32)
