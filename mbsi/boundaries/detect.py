"""Tissue boundary detection."""

from typing import Dict, Optional

import anndata as ad
import numpy as np

from mbsi.utils import build_knn_graph


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
    _, idx = build_knn_graph(coords, k=8)

    boundary_score = np.zeros(len(coords))
    for i in range(len(coords)):
        neighbors = idx[i]
        boundary_score[i] = np.mean(labels[neighbors] != labels[i])

    return {
        "boundary_score": boundary_score.astype(np.float32),
        "labels": labels,
        "note": "Computational hypothesis - Requires experimental validation",
    }
