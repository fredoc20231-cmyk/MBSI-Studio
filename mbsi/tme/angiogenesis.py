"""Angiogenic region scoring."""

from __future__ import annotations

from typing import Dict

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.tme._utils import get_expression, normalize_scores, spatial_smooth

ANGIO_MARKERS = ["VEGFA", "KDR", "PECAM1"]


def score_angiogenic_regions(adata: ad.AnnData, layer: str = "logcounts", k: int = 8) -> Dict:
    """Score angiogenic regions via VEGF/VEGFR/endothelial signature."""
    coords = adata.obsm["spatial"]
    angio = get_expression(adata, ANGIO_MARKERS, layer)
    score = spatial_smooth(coords, normalize_scores(angio), k=k)
    threshold = np.percentile(score, 75)
    mask = score >= threshold
    return {
        "score": score.astype(np.float32),
        "mask": mask,
        "n_niches": int(mask.sum()),
        "mean_score": float(score[mask].mean()) if mask.any() else 0.0,
        "label": "Angiogenic Regions",
        "hypothesis": "computational_hypothesis",
    }


def angiogenesis_table(adata: ad.AnnData, result: Dict) -> pd.DataFrame:
    coords = adata.obsm["spatial"]
    return pd.DataFrame({
        "spot": adata.obs_names,
        "angiogenesis_score": result["score"],
        "is_angiogenic": result["mask"],
        "x": coords[:, 0],
        "y": coords[:, 1],
    })
