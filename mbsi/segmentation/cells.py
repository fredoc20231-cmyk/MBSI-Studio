"""Cell segmentation and Voronoi fallback."""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy.spatial import Voronoi, cKDTree

from mbsi.segmentation.adapters import (
    segment_cells_watershed,
    segment_nuclei_cellpose,
    segment_nuclei_stardist,
)


def segment_cells(
    image: np.ndarray,
    nuclei_mask: Optional[np.ndarray] = None,
    method: str = "cellpose",
    min_size: int = 50,
) -> np.ndarray:
    """Segment cells from image, optionally seeded by nuclei mask."""
    method = (method or "cellpose").lower()
    if method == "imported" and nuclei_mask is not None:
        return nuclei_mask.astype(np.int32)

    if method == "cellpose":
        labels = segment_nuclei_cellpose(image)
        if labels is not None and labels.max() > 0:
            return labels.astype(np.int32)

    if method == "stardist":
        labels = segment_nuclei_stardist(image)
        if labels is not None and labels.max() > 0:
            return labels.astype(np.int32)

    if nuclei_mask is not None and nuclei_mask.max() > 0:
        return nuclei_mask.astype(np.int32)

    return segment_cells_watershed(image, min_size=min_size).astype(np.int32)


def voronoi_label_mask_from_coords(
    coords: np.ndarray,
    shape: tuple[int, int],
    clip_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Rasterize Voronoi regions from centroid coordinates into a label mask."""
    coords = np.asarray(coords, dtype=np.float64)
    h, w = shape
    if len(coords) == 0:
        return np.zeros((h, w), dtype=np.int32)

    Voronoi(coords)
    ys, xs = np.mgrid[0:h, 0:w]
    grid = np.column_stack([xs.ravel(), ys.ravel()])
    tree = cKDTree(coords)
    _, idx = tree.query(grid)
    label_mask = (idx + 1).reshape(h, w).astype(np.int32)

    if clip_mask is not None and clip_mask.shape == (h, w):
        label_mask = label_mask.copy()
        label_mask[~clip_mask.astype(bool)] = 0
    return label_mask


def generate_voronoi_cells(
    coords: np.ndarray,
    clip_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Assign Voronoi-like cell regions from spatial coordinates.

    Returns integer region label per point (n_points,).
    """
    coords = np.asarray(coords, dtype=np.float64)
    if len(coords) == 0:
        return np.array([], dtype=np.int32)
    if len(coords) < 4:
        return np.arange(len(coords), dtype=np.int32)

    vor = Voronoi(coords)
    tree = cKDTree(coords)
    _, nn_idx = tree.query(coords, k=1)
    labels = nn_idx.astype(np.int32)

    if clip_mask is not None and clip_mask.ndim == 1 and len(clip_mask) == len(coords):
        labels = labels.copy()
        labels[~clip_mask.astype(bool)] = -1

    labels = labels.astype(np.int32)
    if hasattr(vor, "vertices"):
        return labels
    return labels
