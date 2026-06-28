"""Spatial signaling graph construction."""

from typing import Dict, List, Tuple

import anndata as ad
import numpy as np
import networkx as nx

from mbsi.utils import build_knn_graph, to_dense_flat


def build_spatial_signaling_graph(
    adata: ad.AnnData,
    ligand_receptor_pairs: List[Tuple[str, str]],
    k_neighbors: int = 10,
) -> Dict:
    """
    Build sender-receiver graph with diffusion-weighted edge flux.
    """
    coords = adata.obsm["spatial"]
    dists, idx = build_knn_graph(coords, k=k_neighbors)

    G = nx.DiGraph()
    flux_table = []

    for lig, rec in ligand_receptor_pairs:
        if lig not in adata.var_names or rec not in adata.var_names:
            continue
        lig_expr = to_dense_flat(adata[:, lig].X)
        rec_expr = to_dense_flat(adata[:, rec].X)

        for i in range(len(coords)):
            for j_idx, j in enumerate(idx[i]):
                w = np.exp(-dists[i, j_idx] ** 2 / (2 * 50 ** 2))
                flux = float(lig_expr[i] * rec_expr[j] * w)
                if flux > 0.01:
                    G.add_edge(i, j, ligand=lig, receptor=rec, flux=flux)
                    flux_table.append({"sender": i, "receiver": j, "ligand": lig, "receptor": rec, "flux": flux})

    return {
        "graph": G,
        "flux_table": flux_table,
        "n_edges": G.number_of_edges(),
        "note": "Computational hypothesis - Requires experimental validation",
    }
