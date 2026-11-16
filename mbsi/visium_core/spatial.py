"""Phase 0/1 — squidpy spatial graph and spatial statistics with BH-FDR."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from .provenance import BlockedAnalysis, require


def bh_fdr(pvals: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (NaN preserved)."""
    p = np.asarray(pvals, dtype=float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    n = pv.size
    if n == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order] * n / np.arange(1, n + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    adj = np.empty(n)
    adj[order] = np.clip(ranked, 0, 1)
    out[ok] = adj
    return out


def build_spatial_graph(adata, params: Dict[str, Any]) -> Dict[str, Any]:
    sq = require("squidpy", "Install squidpy>=1.4 on the scientific service.")
    if "spatial" not in adata.obsm:
        raise BlockedAnalysis("Dataset has no spatial coordinates (obsm['spatial']).", "Upload Space Ranger output with spatial positions.")
    coord_type = params.get("coord_type", "grid")  # Visium hex grid
    kwargs = {"coord_type": coord_type}
    if coord_type == "grid":
        kwargs["n_rings"] = int(params.get("n_rings", 1))
        kwargs["n_neighs"] = int(params.get("n_neighs", 6))
    else:
        kwargs["delaunay"] = bool(params.get("delaunay", True))
    sq.gr.spatial_neighbors(adata, **kwargs)
    return kwargs


def spatially_variable_genes(adata, params: Dict[str, Any]) -> Dict[str, Any]:
    sq = require("squidpy", "Install squidpy>=1.4.")
    graph = build_spatial_graph(adata, params)
    mode = params.get("mode", "moran")
    n_top = int(params.get("n_top", 2000))
    genes = adata.var_names[adata.var["highly_variable"]] if "highly_variable" in adata.var else adata.var_names[:n_top]
    df = sq.gr.spatial_autocorr(adata, mode=mode, genes=list(genes)[:n_top], n_perms=None, copy=True)
    pcol = "pval_norm"
    df["fdr_bh"] = bh_fdr(df[pcol].to_numpy())
    alpha = float(params.get("fdr_alpha", 0.05))
    sig = df[df["fdr_bh"] < alpha].sort_values("fdr_bh")
    return {
        "graph": graph,
        "mode": mode,
        "n_tested": int(len(df)),
        "n_significant": int(len(sig)),
        "fdr_alpha": alpha,
        "svg_table": sig.head(200).reset_index(names="gene").to_dict(orient="records"),
    }


def neighborhood_statistics(adata, params: Dict[str, Any]) -> Dict[str, Any]:
    sq = require("squidpy", "Install squidpy>=1.4.")
    key = params.get("cluster_key", "leiden")
    if key not in adata.obs:
        raise BlockedAnalysis(f"Cluster labels '{key}' are missing.", "Run clustering or niche detection first.")
    build_spatial_graph(adata, params)
    adata.obs[key] = adata.obs[key].astype("category")
    cats = list(adata.obs[key].cat.categories)
    z, counts = sq.gr.nhood_enrichment(adata, cluster_key=key, copy=True, seed=int(params.get("seed", 0)), show_progress_bar=False)
    inter = sq.gr.interaction_matrix(adata, cluster_key=key, copy=True)
    co, intervals = sq.gr.co_occurrence(adata, cluster_key=key, copy=True, show_progress_bar=False)
    ripley = sq.gr.ripley(adata, cluster_key=key, mode=params.get("ripley_mode", "L"), copy=True)
    stat = ripley.get(f"{params.get('ripley_mode', 'L')}_stat")
    return {
        "categories": cats,
        "nhood_enrichment_zscore": np.nan_to_num(z).round(4).tolist(),
        "interaction_matrix": np.asarray(inter).tolist(),
        "co_occurrence_intervals": np.asarray(intervals).round(3).tolist(),
        "co_occurrence": np.asarray(co).round(4).tolist(),
        "ripley": stat.to_dict(orient="records") if stat is not None else [],
    }
