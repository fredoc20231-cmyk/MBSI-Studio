"""Build tissue digital twin state from AnnData."""

from typing import Any, Dict

import anndata as ad
import numpy as np

from mbsi.utils import to_dense_array


def build_tissue_digital_twin(adata: ad.AnnData) -> Dict[str, Any]:
    """Capture current tissue state for simulation."""
    X = to_dense_array(adata.X)
    compartments = {}
    if "compartment" in adata.obs:
        for c in adata.obs["compartment"].unique():
            compartments[str(c)] = float((adata.obs["compartment"] == c).mean())
    else:
        compartments = {"tumor": 0.4, "stroma": 0.3, "immune": 0.2, "necrosis": 0.1}

    return {
        "n_cells": adata.n_obs,
        "n_genes": adata.n_vars,
        "mean_expression": float(X.mean()),
        "compartments": compartments,
        "immune_infiltration": float(compartments.get("immune", 0.2)),
        "resistance_score": float(np.clip(X[:, :5].mean() * 0.1, 0, 1)) if X.shape[1] >= 5 else 0.3,
        "uncertainty": 0.15,
        "warning": "Simulation/hypothesis generation only.",
    }
