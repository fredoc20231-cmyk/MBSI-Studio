"""Spatial gradient detection."""

from __future__ import annotations

from typing import List, Tuple

import anndata as ad
import numpy as np
import pandas as pd


def compute_gradient(
    adata: ad.AnnData,
    mode: str = "domain_centered",
    anchor_key: str = "domain",
    gene: str = "",
) -> Tuple[pd.DataFrame, List[str]]:
    """Compute spatial gradient evidence table."""
    warnings: List[str] = []
    if "spatial" not in adata.obsm:
        return pd.DataFrame(), ["No spatial coordinates in adata.obsm['spatial']."]

    coords = np.asarray(adata.obsm["spatial"], dtype=float)
    mode = (mode or "domain_centered").lower()

    if mode == "domain_centered" and anchor_key in adata.obs.columns:
        centers = {}
        for dom in adata.obs[anchor_key].astype(str).unique():
            mask = adata.obs[anchor_key].astype(str) == dom
            centers[dom] = coords[mask].mean(axis=0)
        dists = []
        for i, dom in enumerate(adata.obs[anchor_key].astype(str)):
            c = centers.get(dom, coords[i])
            dists.append(float(np.linalg.norm(coords[i] - c)))
        adata.obs["gradient_distance"] = dists
    elif mode in ("tumor_margin", "boundary_distance"):
        cx, cy = coords.mean(axis=0)
        adata.obs["gradient_distance"] = np.linalg.norm(coords - np.array([cx, cy]), axis=1)
    elif mode == "custom_anchor" and anchor_key in adata.obs.columns:
        anchor_mask = adata.obs[anchor_key].astype(str).isin(["1", "anchor", "tumor"])
        if anchor_mask.any():
            anchor = coords[anchor_mask].mean(axis=0)
            adata.obs["gradient_distance"] = np.linalg.norm(coords - anchor, axis=1)
        else:
            warnings.append("No anchor spots found — used centroid distance.")
            cx, cy = coords.mean(axis=0)
            adata.obs["gradient_distance"] = np.linalg.norm(coords - np.array([cx, cy]), axis=1)
    else:
        cx, cy = coords.mean(axis=0)
        adata.obs["gradient_distance"] = np.linalg.norm(coords - np.array([cx, cy]), axis=1)

    rows = []
    genes = [gene] if gene and gene in adata.var_names else list(adata.var_names[:20])
    dist = adata.obs["gradient_distance"].values
    for g in genes:
        idx = list(adata.var_names).index(g)
        vals = adata.X[:, idx]
        if hasattr(vals, "toarray"):
            vals = vals.toarray().flatten()
        corr = float(np.corrcoef(dist, np.asarray(vals).flatten())[0, 1]) if len(dist) > 2 else 0.0
        rows.append({"gene": g, "mode": mode, "gradient_correlation": corr, "mean_distance": float(dist.mean())})

    return pd.DataFrame(rows).sort_values("gradient_correlation", key=abs, ascending=False), warnings
