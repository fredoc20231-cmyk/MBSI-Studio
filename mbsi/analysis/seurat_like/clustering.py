"""Clustering for Seurat-like workflow."""

from __future__ import annotations

from typing import Tuple

import anndata as ad

from mbsi.analysis.clustering import run_clustering_method, run_leiden_clustering


def run_leiden(adata: ad.AnnData, resolution: float = 1.0, key_added: str = "cluster") -> Tuple[ad.AnnData, str]:
    """Run Leiden clustering with honest fallback note."""
    adata, note = run_clustering_method(adata, method="Leiden", resolution=resolution, key_added=key_added)
    return adata, note


def run_louvain(adata: ad.AnnData, resolution: float = 1.0, key_added: str = "cluster") -> Tuple[ad.AnnData, str]:
    """Run Louvain clustering with honest fallback when unavailable."""
    adata, note = run_clustering_method(adata, method="Louvain", resolution=resolution, key_added=key_added)
    return adata, note
