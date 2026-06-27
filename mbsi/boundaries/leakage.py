"""Boundary leakage scoring."""

from typing import Dict, List, Optional

import anndata as ad
import numpy as np


def compute_boundary_leakage(
    adata: ad.AnnData,
    marker_sets: Optional[Dict[str, List[str]]] = None,
    boundaries: Optional[Dict] = None,
) -> float:
    """
    Compute epithelial/marker leakage across compartment boundaries.
    """
    if boundaries is None:
        from mbsi.boundaries.detect import detect_tissue_boundaries
        boundaries = detect_tissue_boundaries(adata)

    boundary_score = boundaries["boundary_score"]
    labels = boundaries["labels"]

    if marker_sets is None:
        X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
        marker_expr = X.mean(axis=1)
    else:
        genes = []
        for glist in marker_sets.values():
            genes.extend([g for g in glist if g in adata.var_names])
        genes = list(set(genes))[:10]
        if not genes:
            return 0.0
        X = adata[:, genes].X
        if hasattr(X, "toarray"):
            X = X.toarray()
        marker_expr = X.mean(axis=1)

    # Leakage: high marker expression at boundary regions with label heterogeneity
    leakage = float(np.mean(marker_expr * boundary_score))
    return leakage
