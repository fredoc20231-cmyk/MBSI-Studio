"""Invasive front detection — integrates with mbsi.boundaries."""

from __future__ import annotations

import logging
from typing import Dict, List

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.tme._utils import get_expression, normalize_scores

logger = logging.getLogger(__name__)

TUMOR_MARKERS = ["EPCAM", "KRT8", "MKI67"]
STROMAL_MARKERS = ["ACTA2", "COL1A1", "FAP"]


def detect_invasive_fronts(adata: ad.AnnData, layer: str = "logcounts") -> Dict:
    """Detect invasive fronts using boundary scores + tumor-stroma interface."""
    try:
        from mbsi.boundaries.invasion import detect_invasion_corridors
        corridor = detect_invasion_corridors(adata, TUMOR_MARKERS, STROMAL_MARKERS)
    except Exception as exc:
        logger.warning("detect_invasion_corridors failed (%s); using simplified scoring", exc)
        tumor = get_expression(adata, TUMOR_MARKERS, layer)
        stroma = get_expression(adata, STROMAL_MARKERS, layer)
        corridor = tumor * stroma / (tumor + stroma + 1e-10)

    try:
        from mbsi.boundaries.detect import detect_tissue_boundaries
        bscore = detect_tissue_boundaries(adata)["boundary_score"]
    except Exception as exc:
        logger.warning("detect_tissue_boundaries failed (%s); using zero boundary scores", exc)
        bscore = np.zeros(adata.n_obs)

    score = normalize_scores(corridor + 0.5 * bscore)
    threshold = np.percentile(score, 80)
    mask = score >= threshold
    result = {
        "score": score.astype(np.float32),
        "spatial_vector": score.astype(np.float32),
        "mask": mask,
        "n_niches": int(mask.sum()),
        "mean_score": float(score[mask].mean()) if mask.any() else 0.0,
        "label": "Invasive Fronts",
        "hypothesis": "computational_hypothesis",
    }
    result["table"] = invasion_table(adata, result)
    return result


def invasion_table(adata: ad.AnnData, result: Dict) -> pd.DataFrame:
    coords = adata.obsm["spatial"]
    return pd.DataFrame({
        "spot": adata.obs_names,
        "invasion_score": result["score"],
        "is_invasive_front": result["mask"],
        "x": coords[:, 0],
        "y": coords[:, 1],
    })
