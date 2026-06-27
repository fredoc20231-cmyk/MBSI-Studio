"""ATAC feature integration."""

import anndata as ad
import numpy as np
import pandas as pd


def add_atac_features(adata: ad.AnnData, atac_matrix: pd.DataFrame) -> ad.AnnData:
    """Add ATAC peak accessibility aligned by obs index."""
    adata = adata.copy()
    common = adata.obs_names.intersection(atac_matrix.index)
    if len(common) == 0:
        adata.obsm["atac"] = np.zeros((adata.n_obs, atac_matrix.shape[1]))
    else:
        mat = np.zeros((adata.n_obs, atac_matrix.shape[1]))
        idx = [list(adata.obs_names).index(c) for c in common]
        mat[idx] = atac_matrix.loc[common].values
        adata.obsm["atac"] = mat.astype(np.float32)
    return adata
