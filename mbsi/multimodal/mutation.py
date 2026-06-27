"""Mutation feature integration."""

import anndata as ad
import numpy as np
import pandas as pd


def add_mutation_features(adata: ad.AnnData, mutation_table: pd.DataFrame) -> ad.AnnData:
    adata = adata.copy()
    common = adata.obs_names.intersection(mutation_table.index)
    mat = np.zeros((adata.n_obs, mutation_table.shape[1]))
    if len(common):
        for i, name in enumerate(adata.obs_names):
            if name in mutation_table.index:
                mat[i] = mutation_table.loc[name].values
    adata.obsm["mutation"] = mat.astype(np.float32)
    return adata
