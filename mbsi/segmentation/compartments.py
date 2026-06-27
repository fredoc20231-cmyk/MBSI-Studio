"""Compartment assignment for spots and cells."""

from typing import Dict, Optional

import anndata as ad
import numpy as np
from sklearn.cluster import KMeans

COMPARTMENT_NAMES = ["tumor", "stroma", "immune", "necrosis"]


def infer_compartment_labels(
    adata: ad.AnnData,
    n_compartments: int = 4,
    key: str = "compartment",
) -> ad.AnnData:
    """
    Infer compartment labels from spatial coordinates and expression.

    Placeholder compartment model using k-means on coords + mean expression.
    """
    coords = adata.obsm["spatial"]
    X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    features = np.hstack([coords, X.mean(axis=1, keepdims=True)])
    labels = KMeans(n_clusters=min(n_compartments, len(adata)), random_state=42, n_init=10).fit_predict(features)
    adata = adata.copy()
    adata.obs[key] = [COMPARTMENT_NAMES[i % len(COMPARTMENT_NAMES)] for i in labels]
    adata.obs[f"{key}_id"] = labels.astype(int)
    adata.uns["compartment_note"] = "Computational hypothesis - Requires experimental validation"
    return adata


def assign_spots_to_compartments(
    adata: ad.AnnData,
    compartment_mask: Optional[np.ndarray] = None,
    key: str = "compartment",
) -> ad.AnnData:
    """Assign spots to compartments from mask or inferred labels."""
    adata = adata.copy()
    if compartment_mask is not None and compartment_mask.ndim == 1:
        adata.obs[key] = [COMPARTMENT_NAMES[int(m) % len(COMPARTMENT_NAMES)] for m in compartment_mask]
    else:
        adata = infer_compartment_labels(adata, key=key)
    return adata
