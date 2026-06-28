"""Sender and receiver cell ranking for L-R pairs."""

from __future__ import annotations

from typing import Dict, Tuple

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.communication._utils import get_expression, resolve_gene
from mbsi.utils import build_knn_graph


def rank_sender_receiver(
    adata: ad.AnnData,
    pair: Tuple[str, str],
    k: int = 6,
    layer: str = "logcounts",
    top_n: int = 20,
) -> Dict:
    """Rank sender and receiver spots/cells with communication scores."""
    lig, rec = pair
    lig_e = get_expression(adata, lig, layer)
    rec_e = get_expression(adata, rec, layer)
    coords = adata.obsm["spatial"]
    n = adata.n_obs

    dists, indices = build_knn_graph(coords, k=k)

    sender_scores = lig_e.copy()
    receiver_scores = rec_e.copy()
    edge_flux = []

    for i in range(n):
        for j_idx, j in enumerate(indices[i]):
            w = np.exp(-dists[i, j_idx] ** 2 / (2 * 30.0 ** 2))
            flux = lig_e[i] * rec_e[j] * w
            edge_flux.append({
                "sender_idx": i,
                "receiver_idx": j,
                "sender": adata.obs_names[i],
                "receiver": adata.obs_names[j],
                "ligand": resolve_gene(adata, lig) or lig,
                "receptor": resolve_gene(adata, rec) or rec,
                "flux": float(flux),
                "score": float(flux),
            })

    rows = []
    for i in range(n):
        rows.append({
            "spot": adata.obs_names[i],
            "role": "sender" if sender_scores[i] >= receiver_scores[i] else "receiver",
            "sender_score": float(sender_scores[i]),
            "receiver_score": float(receiver_scores[i]),
            "ligand_expr": float(lig_e[i]),
            "receptor_expr": float(rec_e[i]),
            "x": float(coords[i, 0]),
            "y": float(coords[i, 1]),
        })

    table = pd.DataFrame(rows)
    edge_df = pd.DataFrame(edge_flux).sort_values("flux", ascending=False) if edge_flux else pd.DataFrame()

    top_senders = table.nlargest(top_n, "sender_score")[["spot", "sender_score", "ligand_expr", "x", "y"]]
    top_receivers = table.nlargest(top_n, "receiver_score")[["spot", "receiver_score", "receptor_expr", "x", "y"]]

    return {
        "table": table,
        "edges": edge_df,
        "top_senders": top_senders,
        "top_receivers": top_receivers,
    }
