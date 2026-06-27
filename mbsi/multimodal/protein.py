"""Protein feature integration."""

import anndata as ad
import numpy as np


def add_protein_features(adata: ad.AnnData, protein_matrix: np.ndarray) -> ad.AnnData:
    adata = adata.copy()
    adata.obsm["protein"] = np.asarray(protein_matrix, dtype=np.float32)
    return adata
