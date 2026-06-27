"""Align spatial timepoints."""

from typing import Dict, List

import anndata as ad
import numpy as np
from sklearn.neighbors import NearestNeighbors


def align_spatial_timepoints(adatas: List[ad.AnnData]) -> Dict:
    """
    Align multiple timepoint AnnData objects by spatial coordinates.

    Returns mapping of timepoint index -> aligned reference indices.
    """
    if not adatas:
        return {"alignments": [], "timepoints": []}

    ref_coords = adatas[0].obsm["spatial"]
    alignments = [{"timepoint": 0, "mapping": np.arange(len(ref_coords)).tolist()}]

    for t, adata in enumerate(adatas[1:], start=1):
        coords = adata.obsm["spatial"]
        tree = NearestNeighbors(n_neighbors=1).fit(ref_coords)
        _, idx = tree.kneighbors(coords)
        alignments.append({"timepoint": t, "mapping": idx.flatten().tolist()})

    return {
        "alignments": alignments,
        "timepoints": [f"D{i}" for i in range(len(adatas))],
        "note": "Computational hypothesis - Requires experimental validation",
    }
