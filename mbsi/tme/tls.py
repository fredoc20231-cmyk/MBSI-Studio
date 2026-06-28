"""TLS-like niche detection."""

from __future__ import annotations

from typing import Dict

import anndata as ad
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

from mbsi.tme._utils import get_expression, normalize_scores

TLS_MARKERS = ["MS4A1", "BCL6", "CXCL13", "CD3D"]


def detect_tls_niches(adata: ad.AnnData, layer: str = "logcounts", eps: float = 12.0) -> Dict:
    """Detect TLS-like niches via B/T cell aggregate signature + spatial clustering."""
    coords = adata.obsm["spatial"]
    tls_sig = get_expression(adata, TLS_MARKERS, layer)
    score = normalize_scores(tls_sig)
    threshold = np.percentile(score, 80)
    candidates = score >= threshold
    labels = np.full(adata.n_obs, -1, dtype=int)
    if candidates.sum() >= 3:
        clustering = DBSCAN(eps=eps, min_samples=3).fit(coords[candidates])
        labels[candidates] = clustering.labels_
    niche_ids = [i for i in np.unique(labels) if i >= 0]
    mask = labels >= 0
    return {
        "score": score.astype(np.float32),
        "mask": mask,
        "cluster_labels": labels,
        "n_niches": len(niche_ids),
        "mean_score": float(score[mask].mean()) if mask.any() else 0.0,
        "label": "TLS-like Niches",
        "hypothesis": "computational_hypothesis",
    }


def tls_table(adata: ad.AnnData, result: Dict) -> pd.DataFrame:
    coords = adata.obsm["spatial"]
    return pd.DataFrame({
        "spot": adata.obs_names,
        "tls_score": result["score"],
        "tls_cluster": result["cluster_labels"],
        "is_tls_niche": result["mask"],
        "x": coords[:, 0],
        "y": coords[:, 1],
    })
