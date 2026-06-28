"""Hypoxic niche proxy scoring."""

from __future__ import annotations

from typing import Dict

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.tme._utils import get_expression, normalize_scores, spatial_smooth

HYPOXIA_MARKERS = ["HIF1A", "CA9", "SLC2A1"]


def score_hypoxic_niches(adata: ad.AnnData, layer: str = "logcounts", k: int = 8) -> Dict:
    """Hypoxic niche proxy via HIF/CA9/GLUT1 signature and spatial coherence."""
    coords = adata.obsm["spatial"]
    hyp = get_expression(adata, HYPOXIA_MARKERS, layer)
    score = spatial_smooth(coords, normalize_scores(hyp), k=k)
    threshold = np.percentile(score, 75)
    mask = score >= threshold
    return {
        "score": score.astype(np.float32),
        "mask": mask,
        "n_niches": int(mask.sum()),
        "mean_score": float(score[mask].mean()) if mask.any() else 0.0,
        "label": "Hypoxic Regions",
        "hypothesis": "computational_hypothesis",
    }


def hypoxia_table(adata: ad.AnnData, result: Dict) -> pd.DataFrame:
    coords = adata.obsm["spatial"]
    return pd.DataFrame({
        "spot": adata.obs_names,
        "hypoxia_score": result["score"],
        "is_hypoxic": result["mask"],
        "x": coords[:, 0],
        "y": coords[:, 1],
    })
