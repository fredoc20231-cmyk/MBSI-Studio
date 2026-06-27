"""Tissue boundary detection."""

from typing import Dict, Optional

import anndata as ad
import numpy as np
from sklearn.neighbors import NearestNeighbors


def detect_tissue_boundaries(
    adata: ad.AnnData,
    image: Optional[np.ndarray] = None,
    labels: Optional[np.ndarray] = None,
) -> Dict[str, np.ndarray]:
    """
    Detect tumor-stroma and compartment boundaries.

    Returns boundary scores per observation and boundary edge list.
    """
    coords = adata.obsm["spatial"]
    if labels is None and "compartment" in adata.obs:
        labels = adata.obs["compartment"].astype("category").cat.codes.values
    elif labels is None:
        from mbsi.segmentation.compartments import infer_compartment_labels
        adata = infer_compartment_labels(adata)
        labels = adata.obs["compartment_id"].values

    labels = np.asarray(labels)
    tree = NearestNeighbors(n_neighbors=min(8, len(coords))).fit(coords)
    _, idx = tree.kneighbors(coords)

    boundary_score = np.zeros(len(coords))
    for i in range(len(coords)):
        neighbors = idx[i]
        boundary_score[i] = np.mean(labels[neighbors] != labels[i])

    return {
        "boundary_score": boundary_score.astype(np.float32),
        "labels": labels,
        "note": "Computational hypothesis - Requires experimental validation",
    }
