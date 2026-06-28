"""CAF barrier region detection."""

from __future__ import annotations

from typing import Dict

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.tme._utils import get_expression, normalize_scores, spatial_smooth

CAF_MARKERS = ["ACTA2", "FAP", "COL1A1"]
TUMOR_MARKERS = ["EPCAM", "KRT8"]


def detect_caf_barriers(adata: ad.AnnData, layer: str = "logcounts", k: int = 8) -> Dict:
    """Detect CAF barrier regions (high stromal CAF signature at tumor interface)."""
    coords = adata.obsm["spatial"]
    caf = get_expression(adata, CAF_MARKERS, layer)
    tumor = get_expression(adata, TUMOR_MARKERS, layer)
    interface = caf * (tumor > np.median(tumor)).astype(float)
    score = spatial_smooth(coords, normalize_scores(interface + caf * 0.5), k=k)
    threshold = np.percentile(score, 70)
    mask = score >= threshold
    return {
        "score": score.astype(np.float32),
        "mask": mask,
        "n_niches": int(mask.sum()),
        "mean_score": float(score[mask].mean()) if mask.any() else 0.0,
        "label": "CAF Barriers",
        "hypothesis": "computational_hypothesis",
    }


def caf_barrier_table(adata: ad.AnnData, result: Dict) -> pd.DataFrame:
    coords = adata.obsm["spatial"]
    return pd.DataFrame({
        "spot": adata.obs_names,
        "caf_barrier_score": result["score"],
        "is_caf_barrier": result["mask"],
        "x": coords[:, 0],
        "y": coords[:, 1],
    })
