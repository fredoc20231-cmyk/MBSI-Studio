"""Clinical feature integration."""

import anndata as ad
import numpy as np
import pandas as pd


def add_clinical_features(adata: ad.AnnData, clinical_table: pd.DataFrame) -> ad.AnnData:
    adata = adata.copy()
    # Broadcast sample-level clinical to all cells if single row
    if len(clinical_table) == 1:
        mat = np.tile(clinical_table.values, (adata.n_obs, 1))
    else:
        mat = np.zeros((adata.n_obs, clinical_table.shape[1]))
        for i, name in enumerate(adata.obs_names):
            if name in clinical_table.index:
                mat[i] = clinical_table.loc[name].values
    adata.obsm["clinical"] = mat.astype(np.float32)
    return adata
