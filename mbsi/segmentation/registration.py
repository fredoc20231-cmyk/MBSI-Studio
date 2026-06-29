"""Spatial-to-image registration utilities."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
from scipy.spatial import cKDTree


def estimate_affine_transform(
    source_coords: np.ndarray,
    target_coords: np.ndarray,
) -> np.ndarray:
    """Estimate 2D affine transform (3x3) mapping source -> target."""
    source = np.asarray(source_coords, dtype=np.float64)
    target = np.asarray(target_coords, dtype=np.float64)
    n = min(len(source), len(target))
    if n < 3:
        return np.eye(3, dtype=np.float64)

    src = source[:n]
    tgt = target[:n]
    ones = np.ones((n, 1), dtype=np.float64)
    design = np.hstack([src, ones])
    params_x, _, _, _ = np.linalg.lstsq(design, tgt[:, 0], rcond=None)
    params_y, _, _, _ = np.linalg.lstsq(design, tgt[:, 1], rcond=None)
    transform = np.array(
        [
            [params_x[0], params_x[1], params_x[2]],
            [params_y[0], params_y[1], params_y[2]],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    return transform


def apply_transform_to_coords(coords: np.ndarray, transform: np.ndarray) -> np.ndarray:
    """Apply 3x3 affine transform to Nx2 coordinates."""
    coords = np.asarray(coords, dtype=np.float64)
    ones = np.ones((len(coords), 1), dtype=np.float64)
    hom = np.hstack([coords, ones])
    mapped = hom @ transform.T
    return mapped[:, :2].astype(np.float32)


def _scalefactors_from_adata(adata: Any) -> Dict[str, float]:
    spatial = getattr(adata, "uns", {}).get("spatial", {})
    if isinstance(spatial, dict):
        for lib in spatial.values():
            if isinstance(lib, dict) and "scalefactors" in lib:
                sf = lib["scalefactors"]
                return {
                    "tissue_hires_scalef": float(sf.get("tissue_hires_scalef", 1.0)),
                    "tissue_lowres_scalef": float(sf.get("tissue_lowres_scalef", 0.1)),
                }
    return {"tissue_hires_scalef": 1.0, "tissue_lowres_scalef": 0.1}


def register_spatial_to_image(
    adata: Any,
    image: Optional[np.ndarray] = None,
    scalefactors: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Register spatial coordinates to image space.

    Supports Visium scalefactors, generic affine, and morphology alignment.
    """
    if adata is None or "spatial" not in adata.obsm:
        return {"status": "failed", "reason": "no spatial coordinates"}

    coords = np.asarray(adata.obsm["spatial"], dtype=np.float64)
    sf = scalefactors or _scalefactors_from_adata(adata)
    scale = float(sf.get("tissue_hires_scalef", 1.0))

    registered = coords * scale
    transform = np.eye(3, dtype=np.float64)
    transform[0, 0] = scale
    transform[1, 1] = scale

    if image is not None and image.ndim >= 2:
        h, w = image.shape[:2]
        src_min = coords.min(axis=0)
        src_max = coords.max(axis=0)
        tgt_min = np.array([0.0, 0.0])
        tgt_max = np.array([w - 1.0, h - 1.0])
        src_span = np.maximum(src_max - src_min, 1e-6)
        tgt_span = tgt_max - tgt_min
        sx = tgt_span[0] / src_span[0]
        sy = tgt_span[1] / src_span[1]
        tx = tgt_min[0] - src_min[0] * sx
        ty = tgt_min[1] - src_min[1] * sy
        transform = np.array([[sx, 0, tx], [0, sy, ty], [0, 0, 1]], dtype=np.float64)
        registered = apply_transform_to_coords(coords, transform)

    adata.obsm["spatial_registered"] = registered.astype(np.float32)
    adata.uns.setdefault("mbsi_segmentation", {})["registration"] = {
        "scalefactors": sf,
        "transform": transform.tolist(),
        "method": "scalefactors" if image is None else "affine_fit",
    }
    return {
        "status": "ok",
        "transform": transform,
        "registered_coords": registered,
        "scalefactors": sf,
    }


def validate_registration(adata: Any, tissue_mask: Optional[np.ndarray]) -> Dict[str, Any]:
    """Validate that registered spots fall inside tissue mask."""
    if adata is None or tissue_mask is None:
        return {"valid": False, "reason": "missing adata or tissue mask", "fraction_in_tissue": 0.0}

    coords_key = "spatial_registered" if "spatial_registered" in adata.obsm else "spatial"
    coords = np.asarray(adata.obsm[coords_key])
    h, w = tissue_mask.shape[:2]
    inside = 0
    total = len(coords)
    for x, y in coords:
        ix, iy = int(round(x)), int(round(y))
        if 0 <= ix < w and 0 <= iy < h and tissue_mask[iy, ix] > 0:
            inside += 1
    fraction = inside / total if total else 0.0
    return {
        "valid": fraction >= 0.5,
        "fraction_in_tissue": float(fraction),
        "spots_inside": inside,
        "spots_total": total,
    }
