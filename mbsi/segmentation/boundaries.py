"""Region boundary detection and invasion-front scoring."""

from __future__ import annotations

from typing import Any, Dict, Optional

import anndata as ad
import numpy as np
from skimage.segmentation import find_boundaries
from sklearn.neighbors import NearestNeighbors


def extract_region_boundaries(labels: np.ndarray) -> np.ndarray:
    """Extract boundary pixels from integer label mask."""
    labels = np.asarray(labels)
    if labels.ndim == 1:
        return (labels != np.roll(labels, -1)).astype(np.uint8)
    return find_boundaries(labels, mode="outer").astype(np.uint8)


def compute_tumor_stroma_boundary(
    adata: ad.AnnData,
    compartment_key: str = "compartment",
) -> Dict[str, np.ndarray]:
    """Compute tumor-stroma interface scores per observation."""
    coords = np.asarray(adata.obsm["spatial"])
    if compartment_key not in adata.obs:
        return {"boundary_score": np.zeros(len(coords), dtype=np.float32), "labels": np.zeros(len(coords))}

    labels = adata.obs[compartment_key].astype(str).values
    tumor = np.char.find(labels.astype(str), "tumor") >= 0
    stroma = np.char.find(labels.astype(str), "stroma") >= 0
    numeric = np.zeros(len(labels), dtype=np.int32)
    numeric[tumor] = 1
    numeric[stroma] = 2

    tree = NearestNeighbors(n_neighbors=min(8, len(coords))).fit(coords)
    _, idx = tree.kneighbors(coords)
    boundary_score = np.zeros(len(coords), dtype=np.float32)
    for i in range(len(coords)):
        neighbors = idx[i]
        boundary_score[i] = float(np.mean(numeric[neighbors] != numeric[i]))
    return {"boundary_score": boundary_score, "labels": numeric}


def compute_invasion_front_score(
    adata: ad.AnnData,
    boundary: Optional[Dict[str, np.ndarray]] = None,
) -> np.ndarray:
    """Score invasion front as high boundary score at tumor-stroma interface."""
    if boundary is None:
        boundary = compute_tumor_stroma_boundary(adata)
    scores = np.asarray(boundary.get("boundary_score", []), dtype=np.float32)
    labels = np.asarray(boundary.get("labels", []))
    invasion = scores.copy()
    invasion[labels == 0] = 0.0
    return invasion.astype(np.float32)


def compute_boundary_confidence(
    boundary: Dict[str, np.ndarray],
    evidence: Optional[Dict[str, Any]] = None,
) -> float:
    """Aggregate boundary confidence from score distribution and evidence."""
    scores = np.asarray(boundary.get("boundary_score", []), dtype=np.float32)
    if len(scores) == 0:
        return 0.0
    base = float(np.clip(scores.mean() * 100, 0, 100))
    if evidence and evidence.get("segmentation_qc_pass"):
        base = min(100.0, base + 10.0)
    return round(base, 1)


def detect_boundaries(
    mask_or_labels: np.ndarray,
    adata: Optional[ad.AnnData] = None,
) -> Dict[str, Any]:
    """Detect boundaries from mask/labels or compartment-aware adata."""
    mask_or_labels = np.asarray(mask_or_labels)
    if adata is not None and "compartment" in adata.obs:
        boundary = compute_tumor_stroma_boundary(adata)
        boundary["boundary_map"] = extract_region_boundaries(mask_or_labels) if mask_or_labels.ndim >= 2 else mask_or_labels
        boundary["invasion_front"] = compute_invasion_front_score(adata, boundary)
        boundary["confidence"] = compute_boundary_confidence(boundary)
        return boundary

    if mask_or_labels.ndim == 1:
        return {
            "boundary_score": extract_region_boundaries(mask_or_labels).astype(np.float32),
            "labels": mask_or_labels,
        }
    bmap = extract_region_boundaries(mask_or_labels)
    return {"boundary_map": bmap, "boundary_score": bmap.astype(np.float32)}
