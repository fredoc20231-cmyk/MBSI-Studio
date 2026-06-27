"""Membrane receptor and ligand field models."""

from typing import List, Optional

import anndata as ad
import numpy as np
from sklearn.neighbors import NearestNeighbors


def estimate_membrane_receptor_maps(
    cell_adata: ad.AnnData,
    receptor_genes: List[str],
) -> np.ndarray:
    """Estimate membrane receptor score per cell (n_cells, n_receptors)."""
    genes = [g for g in receptor_genes if g in cell_adata.var_names]
    if not genes:
        return np.zeros((cell_adata.n_obs, len(receptor_genes)))
    X = cell_adata[:, genes].X
    if hasattr(X, "toarray"):
        X = X.toarray()
    return np.asarray(X, dtype=np.float32)


def estimate_secreted_ligand_fields(
    cell_adata: ad.AnnData,
    ligand_genes: List[str],
    sigma: float = 50.0,
) -> np.ndarray:
    """
    Estimate extracellular ligand field by Gaussian smoothing ligand expression spatially.
    """
    genes = [g for g in ligand_genes if g in cell_adata.var_names]
    coords = cell_adata.obsm["spatial"]
    n = cell_adata.n_obs
    if not genes:
        return np.zeros((n, len(ligand_genes)))

    X = cell_adata[:, genes].X
    if hasattr(X, "toarray"):
        X = X.toarray()

    tree = NearestNeighbors(n_neighbors=min(15, n)).fit(coords)
    dists, idx = tree.kneighbors(coords)
    fields = np.zeros_like(X)
    for i in range(n):
        w = np.exp(-dists[i] ** 2 / (2 * sigma ** 2))
        w /= w.sum() + 1e-10
        fields[i] = (X[idx[i]] * w[:, None]).sum(axis=0)
    return fields.astype(np.float32)
