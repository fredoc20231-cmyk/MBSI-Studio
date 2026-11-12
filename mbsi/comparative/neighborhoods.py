"""Descriptive within-section population neighborhood summaries."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from .preview import spatial_coordinates, _labels


def neighborhood_matrix(adata, label_key: str, k: int = 6,
                        max_units: int = 100000) -> pd.DataFrame:
    """Directed k-nearest-neighbor contacts by annotation.

    Returns row-normalized observed neighbor fractions, NOT enrichment p-values.
    Neighborhoods are defined separately for each tissue.
    """
    coords = spatial_coordinates(adata)
    if coords is None:
        raise ValueError("Valid 2-D spatial coordinates are required")
    if adata.n_obs > max_units:
        raise ValueError(f"Neighborhood preview supports <= {max_units} observations")
    if adata.n_obs < 3:
        raise ValueError("At least three spatial units are required")
    if not (1 <= k < adata.n_obs):
        raise ValueError("k must be at least 1 and less than number of units")
    labels = _labels(adata, label_key).to_numpy()
    names = sorted(set(labels))
    tree = cKDTree(coords)
    _, indices = tree.query(coords, k=k + 1)
    if indices.ndim == 1:
        indices = indices[:, None]
    # Remove the self match, even when coordinate duplicates exist.
    edges = []
    for i, neighbors in enumerate(indices):
        valid = [int(j) for j in neighbors if int(j) != i][:k]
        edges.extend((labels[i], labels[j]) for j in valid)
    table = pd.DataFrame(edges, columns=["source", "neighbor"])
    counts = pd.crosstab(table["source"], table["neighbor"])
    counts = counts.reindex(index=names, columns=names, fill_value=0)
    fractions = counts.div(counts.sum(axis=1).replace(0, np.nan), axis=0)
    return fractions.fillna(0.0)
