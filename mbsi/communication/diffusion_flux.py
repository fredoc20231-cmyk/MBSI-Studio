"""Diffusion-aware signaling flux fields."""

from __future__ import annotations

import anndata as ad
import numpy as np

from mbsi.communication._utils import get_expression, resolve_gene
from mbsi.utils import build_knn_graph


def compute_diffusion_flux(
    adata: ad.AnnData,
    ligand: str,
    receptor: str,
    k: int = 6,
    layer: str = "logcounts",
    sigma: float = 35.0,
) -> np.ndarray:
    """
    Compute spatial diffusion flux field: ligand secretion diffusing toward receptor sinks.

    Returns per-spot/cell flux magnitude array (n_obs,).
    """
    lig_e = get_expression(adata, ligand, layer)
    rec_e = get_expression(adata, receptor, layer)
    coords = adata.obsm["spatial"]
    n = adata.n_obs

    dists, indices = build_knn_graph(coords, k=k)

    flux = np.zeros(n, dtype=float)
    for i in range(n):
        incoming = 0.0
        for j_idx, j in enumerate(indices[i]):
            w = np.exp(-dists[i, j_idx] ** 2 / (2 * sigma ** 2))
            incoming += lig_e[j] * rec_e[i] * w
        flux[i] = incoming + lig_e[i] * rec_e[i] * 0.1

    if flux.max() > 0:
        flux = flux / flux.max()
    return flux.astype(np.float32)
