"""Receptor activation flux from ligand fields."""

from typing import List

import anndata as ad
import numpy as np


def compute_receptor_activation_flux(
    adata: ad.AnnData,
    ligand_field: np.ndarray,
    receptor_genes: List[str],
) -> np.ndarray:
    """
    Compute receptor activation flux = ligand field * receptor expression.
    """
    genes = [g for g in receptor_genes if g in adata.var_names]
    if not genes or ligand_field.size == 0:
        return np.zeros((adata.n_obs, len(receptor_genes)))

    X = adata[:, genes].X
    if hasattr(X, "toarray"):
        X = X.toarray()

    n_lig = ligand_field.shape[1] if ligand_field.ndim > 1 else 1
    n_rec = X.shape[1]
    flux = np.zeros((adata.n_obs, n_rec))
    for j in range(n_rec):
        li = min(j, n_lig - 1)
        lig = ligand_field[:, li] if ligand_field.ndim > 1 else ligand_field
        flux[:, j] = lig * X[:, j]
    return flux.astype(np.float32)
