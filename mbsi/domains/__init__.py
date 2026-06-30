"""Spatial domain detection methods."""

from __future__ import annotations

from typing import List, Tuple

import anndata as ad
import pandas as pd

from mbsi.analysis.clustering import run_clustering_method, run_neighbors, run_pca


def detect_domains(
    adata: ad.AnnData,
    method: str = "leiden",
    resolution: float = 0.8,
    n_neighbors: int = 15,
) -> Tuple[ad.AnnData, pd.DataFrame, List[str]]:
    """Run domain detection; returns (adata, domain_summary, warnings)."""
    warnings: List[str] = []
    adata = adata.copy()
    method = (method or "leiden").lower()

    if "X_pca" not in adata.obsm:
        adata = run_pca(adata, n_comps=min(30, adata.n_vars - 1))
    if "connectivities" not in adata.obsp:
        adata = run_neighbors(adata, n_neighbors=min(n_neighbors, adata.n_obs - 1))

    method_map = {
        "leiden": "Leiden",
        "louvain": "Louvain",
        "stclust": "Spatial graph",
        "bayesspace": "BayesSpace-style",
        "graphst": "GraphST adapter mode",
        "bayesspace_graphst": "BayesSpace-style",
        "mbsi_graph": "Spatial graph",
        "mbsi": "Spatial graph",
    }
    cluster_method = method_map.get(method, "Leiden")
    adata, note = run_clustering_method(adata, method=cluster_method, resolution=resolution, key_added="domain")
    if note:
        warnings.append(note)

    summary = adata.obs["domain"].value_counts().reset_index()
    summary.columns = ["domain", "n_spots"]
    return adata, summary, warnings
