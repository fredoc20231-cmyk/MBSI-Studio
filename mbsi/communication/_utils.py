"""Shared helpers for communication module."""

from __future__ import annotations

from typing import List, Optional

import anndata as ad
import numpy as np

GENE_ALIASES = {
    "CXCR4": ["CXCR4"],
    "TGFBR1": ["TGFBR1", "TGFBR2", "TGFBR"],
    "PD-L1": ["CD274", "PDL1"],
    "PD1": ["PDCD1", "PD1"],
    "VEGFR2": ["KDR", "VEGFR2", "FLK1"],
}


def resolve_gene(adata: ad.AnnData, gene: str) -> Optional[str]:
    if gene in adata.var_names:
        return gene
    for alias in GENE_ALIASES.get(gene, []):
        if alias in adata.var_names:
            return alias
    matches = [g for g in adata.var_names if gene.upper() in g.upper()]
    return matches[0] if matches else None


def get_expression(adata: ad.AnnData, gene: str, layer: str = "logcounts") -> np.ndarray:
    g = resolve_gene(adata, gene)
    if g is None:
        return np.zeros(adata.n_obs)
    if layer in adata.layers:
        x = adata[:, g].layers[layer]
    else:
        x = adata[:, g].X
    return np.asarray(x.toarray() if hasattr(x, "toarray") else x).flatten().astype(float)
