"""Phase 2 — spatially-aware domains/niches via a joint expression + spatial graph."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from .provenance import BlockedAnalysis, require
from .spatial import build_spatial_graph


def spatial_niches(adata, params: Dict[str, Any]) -> Dict[str, Any]:
    sc = require("scanpy", "Install scanpy.")
    if "X_pca" not in adata.obsm:
        raise BlockedAnalysis("PCA embedding missing.", "Run preprocessing (normalize, HVG, PCA) first.")
    alpha = float(params.get("spatial_weight", 0.3))
    resolution = float(params.get("resolution", 0.8))
    if "connectivities" not in adata.obsp:
        sc.pp.neighbors(adata, n_neighbors=int(params.get("n_neighbors", 15)))
    graph = build_spatial_graph(adata, params)
    expr = adata.obsp["connectivities"]
    spat = adata.obsp["spatial_connectivities"]
    joint = (1 - alpha) * expr + alpha * spat
    sc.tl.leiden(adata, adjacency=joint, resolution=resolution, key_added="spatial_niche", random_state=int(params.get("seed", 0)))
    labels = adata.obs["spatial_niche"].astype(str)
    sens = []
    for w in params.get("sensitivity_weights", [0.0, 0.15, 0.3, 0.5]):
        j = (1 - w) * expr + w * spat
        key = f"_niche_w{w}"
        sc.tl.leiden(adata, adjacency=j, resolution=resolution, key_added=key, random_state=0)
        from sklearn.metrics import adjusted_rand_score

        sens.append({"spatial_weight": w, "n_niches": int(adata.obs[key].nunique()), "ari_vs_selected": float(adjusted_rand_score(labels, adata.obs[key]))})
        del adata.obs[key]
    counts = labels.value_counts()
    return {
        "method": "joint_graph_leiden",
        "graph": graph,
        "spatial_weight": alpha,
        "n_niches": int(counts.size),
        "niche_sizes": {k: int(v) for k, v in counts.items()},
        "per_spot_niche": dict(zip(adata.obs_names[:5000].tolist(), labels[:5000].tolist())),
        "sensitivity": sens,
        "stable": bool(np.mean([s["ari_vs_selected"] for s in sens]) > 0.6),
    }
