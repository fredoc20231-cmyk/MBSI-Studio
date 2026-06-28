"""Immune-excluded niche detection."""

from __future__ import annotations

from typing import Dict

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.tme._utils import get_expression, normalize_scores, spatial_smooth

IMMUNE_MARKERS = ["CD8A", "CD3D", "MS4A1"]
TUMOR_MARKERS = ["EPCAM", "KRT8", "MKI67"]


def detect_immune_exclusion(
    adata: ad.AnnData,
    layer: str = "logcounts",
    k: int = 8,
) -> Dict:
    """Detect immune-excluded niches (high tumor, low immune, spatially coherent)."""
    coords = adata.obsm["spatial"]
    tumor = get_expression(adata, TUMOR_MARKERS, layer)
    immune = get_expression(adata, IMMUNE_MARKERS, layer)
    raw = tumor / (immune + 0.5)
    score = spatial_smooth(coords, normalize_scores(raw), k=k)
    threshold = np.percentile(score, 75)
    mask = score >= threshold
    result = {
        "score": score.astype(np.float32),
        "spatial_vector": score.astype(np.float32),
        "mask": mask,
        "n_niches": int(mask.sum()),
        "mean_score": float(score[mask].mean()) if mask.any() else 0.0,
        "label": "Immune Exclusion",
        "hypothesis": "computational_hypothesis",
    }
    result["table"] = immune_exclusion_table(adata, result)
    return result


def immune_exclusion_table(adata: ad.AnnData, result: Dict) -> pd.DataFrame:
    coords = adata.obsm["spatial"]
    return pd.DataFrame({
        "spot": adata.obs_names,
        "immune_exclusion_score": result["score"],
        "is_excluded_niche": result["mask"],
        "x": coords[:, 0],
        "y": coords[:, 1],
    })
