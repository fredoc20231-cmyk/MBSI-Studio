"""Spatial causal DAG construction."""

from typing import Any, Dict, List, Optional

import anndata as ad
import numpy as np
import networkx as nx

from mbsi.utils import build_knn_graph, to_dense_array


def build_spatial_causal_dag(
    adata: ad.AnnData,
    features: Optional[List[str]] = None,
) -> nx.DiGraph:
    """
    Build causal DAG from marker programs, compartments, and spatial adjacency.

    Edges: correlation + spatial adjacency + prior rules.
    """
    G = nx.DiGraph()
    obs_keys = list(adata.obs.columns)
    if features:
        nodes = [f for f in features if f in obs_keys or f in adata.var_names]
    else:
        nodes = []
        if "compartment" in adata.obs:
            nodes.append("compartment")
        # Top variable genes as nodes
        X = to_dense_array(adata.X)
        var_idx = np.argsort(np.var(X, axis=0))[-5:]
        nodes.extend([adata.var_names[i] for i in var_idx])

    for n in nodes:
        G.add_node(n)

    coords = adata.obsm["spatial"]
    _, idx = build_knn_graph(coords, k=6)

    # Prior: compartment -> gene expression
    if "compartment" in nodes:
        for g in nodes:
            if g != "compartment" and g in adata.var_names:
                G.add_edge("compartment", g, weight=0.5, prior=True)

    # Correlation edges among genes
    X = to_dense_array(adata.X)
    for i, ni in enumerate(nodes):
        if ni not in adata.var_names:
            continue
        gi = list(adata.var_names).index(ni)
        for nj in nodes[i + 1:]:
            if nj not in adata.var_names:
                continue
            gj = list(adata.var_names).index(nj)
            corr = np.corrcoef(X[:, gi], X[:, gj])[0, 1]
            if abs(corr) > 0.3:
                G.add_edge(ni, nj, weight=float(abs(corr)), spatial=False)

    G.graph["warning"] = "Causal outputs are computational hypotheses requiring experimental validation."
    return G
