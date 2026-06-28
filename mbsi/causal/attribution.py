"""Causal attribution and driver ranking."""

from typing import Any, Dict, List

import anndata as ad
import networkx as nx
import numpy as np

from mbsi.utils import to_dense_array


def rank_causal_drivers(dag: nx.DiGraph, outcome_node: str) -> List[Dict[str, Any]]:
    """Rank upstream nodes by path weight to outcome."""
    if outcome_node not in dag:
        return []
    drivers = []
    for node in dag.nodes():
        if node == outcome_node:
            continue
        try:
            paths = list(nx.all_simple_paths(dag, node, outcome_node, cutoff=3))
        except nx.NetworkXError:
            paths = []
        if paths:
            score = max(
                np.prod([dag.get_edge_data(p[i], p[i + 1], {}).get("weight", 0.1) for i in range(len(p) - 1)])
                for p in paths
            )
            drivers.append({"node": node, "score": float(score)})
    drivers.sort(key=lambda x: x["score"], reverse=True)
    return drivers


def compute_spatial_attribution(adata: ad.AnnData, outcome_score: np.ndarray) -> np.ndarray:
    """
    Attribute outcome score to genes via correlation (simple attribution map per cell).
    """
    X = to_dense_array(adata.X)
    attrs = np.zeros(X.shape[1])
    for g in range(X.shape[1]):
        corr = np.corrcoef(X[:, g], outcome_score)[0, 1]
        attrs[g] = corr if not np.isnan(corr) else 0.0
    return attrs.astype(np.float32)
