"""Variable feature selection for Seurat-like workflow."""

from __future__ import annotations

import anndata as ad

from mbsi.analysis.preprocessing import select_hvgs


def find_variable_features(adata: ad.AnnData, n_top_genes: int = 2000) -> ad.AnnData:
    """Find highly variable genes; delegates to mbsi.analysis.preprocessing."""
    return select_hvgs(adata, n_top_genes=n_top_genes)
