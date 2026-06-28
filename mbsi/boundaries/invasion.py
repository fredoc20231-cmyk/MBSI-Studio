"""Invasion corridor and immune exclusion detection."""

from typing import List

import anndata as ad
import numpy as np

from mbsi.utils import to_dense_array


def detect_invasion_corridors(
    adata: ad.AnnData,
    tumor_markers: List[str],
    stromal_markers: List[str],
) -> np.ndarray:
    """Detect invasion corridor score per cell/spot."""
    t_genes = [g for g in tumor_markers if g in adata.var_names]
    s_genes = [g for g in stromal_markers if g in adata.var_names]
    if not t_genes or not s_genes:
        return np.zeros(adata.n_obs)

    X = to_dense_array(adata.X)
    t_idx = [list(adata.var_names).index(g) for g in t_genes]
    s_idx = [list(adata.var_names).index(g) for g in s_genes]
    tumor = X[:, t_idx].mean(axis=1)
    stroma = X[:, s_idx].mean(axis=1)
    corridor = tumor * stroma / (tumor + stroma + 1e-10)
    return corridor.astype(np.float32)


def detect_immune_exclusion_zones(
    adata: ad.AnnData,
    tumor_markers: List[str],
    immune_markers: List[str],
) -> np.ndarray:
    """Detect immune exclusion score (high tumor, low immune at boundary)."""
    from mbsi.boundaries.detect import detect_tissue_boundaries
    boundaries = detect_tissue_boundaries(adata)
    bscore = boundaries["boundary_score"]

    t_genes = [g for g in tumor_markers if g in adata.var_names]
    i_genes = [g for g in immune_markers if g in adata.var_names]
    if not t_genes:
        return np.zeros(adata.n_obs)

    X = to_dense_array(adata.X)
    t_idx = [list(adata.var_names).index(g) for g in t_genes]
    tumor = X[:, t_idx].mean(axis=1)
    immune = X[:, [list(adata.var_names).index(g) for g in i_genes]].mean(axis=1) if i_genes else np.zeros(adata.n_obs)

    exclusion = bscore * tumor / (immune + 1.0)
    return exclusion.astype(np.float32)
