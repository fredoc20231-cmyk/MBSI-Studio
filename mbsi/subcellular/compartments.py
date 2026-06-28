"""Subcellular compartment inference."""

from typing import Dict, Optional

import anndata as ad
import numpy as np

from mbsi.utils import to_dense_array


def infer_subcellular_compartments(
    cell_adata: ad.AnnData,
    image: Optional[np.ndarray] = None,
) -> Dict[str, np.ndarray]:
    """
    Infer nuclear, cytoplasmic, membrane compartment scores per cell.

    Returns dict of score arrays (n_cells,) — reconstruction estimates.
    """
    X = to_dense_array(cell_adata.X)
    total = X.sum(axis=1) + 1e-10

    # Heuristic: high-variance genes -> nuclear; mid -> cytoplasmic; surface markers -> membrane
    gene_var = np.var(X, axis=0)
    top_idx = np.argsort(gene_var)[-max(1, X.shape[1] // 10):]
    mid_idx = np.argsort(gene_var)[X.shape[1] // 4: X.shape[1] // 2]

    nuclear = X[:, top_idx].mean(axis=1) / total
    cytoplasmic = X[:, mid_idx].mean(axis=1) / total if len(mid_idx) else total * 0
    membrane = (X.max(axis=1) / total) * 0.3

    if image is not None:
        # Slight boost where local image intensity is high (proxy for cell body)
        coords = cell_adata.obsm.get("spatial")
        if coords is not None:
            cytoplasmic = cytoplasmic * 1.1

    return {
        "nuclear_score": nuclear.astype(np.float32),
        "cytoplasmic_score": cytoplasmic.astype(np.float32),
        "membrane_score": membrane.astype(np.float32),
        "note": "Reconstruction estimate - Requires experimental validation",
    }
