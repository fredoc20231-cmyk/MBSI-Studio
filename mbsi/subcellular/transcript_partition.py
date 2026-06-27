"""Transcript partitioning across subcellular compartments."""

from typing import Dict, List

import anndata as ad
import numpy as np


def partition_transcripts_by_compartment(
    cell_adata: ad.AnnData,
    compartments: Dict[str, np.ndarray],
) -> ad.AnnData:
    """
    Partition expression into compartment-level estimates.

    Adds obs columns: nuclear_expr, cytoplasmic_expr, membrane_expr.
    """
    adata = cell_adata.copy()
    X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)

    nuc = compartments.get("nuclear_score", np.ones(adata.n_obs) * 0.33)
    cyto = compartments.get("cytoplasmic_score", np.ones(adata.n_obs) * 0.33)
    mem = compartments.get("membrane_score", np.ones(adata.n_obs) * 0.33)
    norm = nuc + cyto + mem + 1e-10

    adata.obs["nuclear_expr"] = (X.sum(axis=1) * nuc / norm).astype(np.float32)
    adata.obs["cytoplasmic_expr"] = (X.sum(axis=1) * cyto / norm).astype(np.float32)
    adata.obs["membrane_expr"] = (X.sum(axis=1) * mem / norm).astype(np.float32)
    adata.uns["subcellular_note"] = "Inferred compartment-level estimates"
    return adata
