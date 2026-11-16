"""Phase 5 — cell-cell interaction layer (colocalization + ligand-receptor), hypothesis-level only."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from .provenance import BlockedAnalysis, require
from .spatial import bh_fdr, build_spatial_graph


def cell_interactions(adata, params: Dict[str, Any]) -> Dict[str, Any]:
    sq = require("squidpy", "Install squidpy>=1.4 (and omnipath for ligand-receptor databases).")
    key = params.get("cluster_key", "spatial_niche")
    if key not in adata.obs:
        raise BlockedAnalysis(f"Confirmed labels '{key}' are missing.", "Run niche detection or annotate cell types first; LR analysis only runs on confirmed labels.")
    build_spatial_graph(adata, params)
    adata.obs[key] = adata.obs[key].astype("category")
    cats = list(adata.obs[key].cat.categories)
    z, _ = sq.gr.nhood_enrichment(adata, cluster_key=key, copy=True, show_progress_bar=False)
    z = np.nan_to_num(z)
    min_z = float(params.get("min_colocalization_z", 2.0))
    pairs = [(cats[i], cats[j]) for i in range(len(cats)) for j in range(len(cats)) if z[i, j] >= min_z]
    lr: Any = []
    try:
        res = sq.gr.ligrec(adata, cluster_key=key, n_perms=int(params.get("n_perms", 1000)), copy=True, use_raw=False, show_progress_bar=False, seed=0)
        pv = res["pvalues"].stack([0, 1], future_stack=True) if hasattr(res["pvalues"], "stack") else None
        means = res["means"].stack([0, 1], future_stack=True)
        if pv is not None:
            df = pv.rename("pvalue").to_frame().join(means.rename("mean")).dropna().reset_index()
            df.columns = ["ligand", "receptor", "sender", "receiver", "pvalue", "mean"]
            df = df[[(s, r) in pairs for s, r in zip(df["sender"], df["receiver"])]]
            df["fdr_bh"] = bh_fdr(df["pvalue"].to_numpy())
            lr = df.sort_values("fdr_bh").head(200).round(6).to_dict(orient="records")
    except Exception as exc:  # database download or label issues
        lr = {"status": "blocked", "reason": str(exc)}
    return {
        "evidence_level": "hypothesis",
        "colocalization_zscore": z.round(3).tolist(),
        "categories": cats,
        "colocalized_pairs": [list(p) for p in pairs],
        "ligand_receptor": lr,
        "caveat": "Interactions are hypotheses from expression and proximity; they are not evidence of signalling.",
    }
