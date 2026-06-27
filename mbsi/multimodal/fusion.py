"""Multimodal fusion core."""

from typing import Any, Dict, Optional

import anndata as ad
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


def fuse_rna_image_protein(
    adata: ad.AnnData,
    image_features: Optional[np.ndarray] = None,
    protein: Optional[np.ndarray] = None,
) -> ad.AnnData:
    """Fuse RNA with optional image and protein features into obsm."""
    adata = adata.copy()
    X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    blocks = [X]
    if image_features is not None:
        blocks.append(np.atleast_2d(image_features))
        adata.obsm["image_features"] = image_features
    if protein is not None:
        blocks.append(np.atleast_2d(protein))
        adata.obsm["protein"] = protein
    fused = np.hstack(blocks)
    adata.obsm["multimodal_raw"] = fused.astype(np.float32)
    return adata


def build_multimodal_embedding(adata: ad.AnnData, n_components: int = 20) -> np.ndarray:
    """Build PCA embedding from multimodal features."""
    if "multimodal_raw" in adata.obsm:
        X = adata.obsm["multimodal_raw"]
    else:
        X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    n_components = min(n_components, X.shape[0], X.shape[1])
    emb = PCA(n_components=n_components, random_state=42).fit_transform(StandardScaler().fit_transform(X))
    return emb.astype(np.float32)
