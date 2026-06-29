"""Tissue segmentation from H&E or coordinate-based fallback."""

from typing import Optional

import numpy as np
from sklearn.cluster import KMeans

from mbsi.segmentation.adapters import (
    segment_tissue_adaptive,
    segment_tissue_otsu,
    segment_tissue_sam,
)


def segment_tissue(
    image: Optional[np.ndarray] = None,
    coords: Optional[np.ndarray] = None,
    method: str = "otsu",
    smoothing: float = 1.0,
    min_size: int = 100,
) -> np.ndarray:
    """
    Segment tissue mask from image or density-based fallback on coordinates.

    Returns binary tissue mask (H x W) or region labels per spot/cell index.
    """
    if image is not None:
        method = (method or "otsu").lower()
        if method == "adaptive":
            mask = segment_tissue_adaptive(image, min_size=min_size)
        elif method == "sam":
            mask = segment_tissue_sam(image)
            if mask is None:
                mask = segment_tissue_otsu(image, min_size=min_size)
        else:
            mask = segment_tissue_otsu(image, min_size=min_size)
        if smoothing > 1.0:
            from scipy import ndimage
            mask = ndimage.binary_opening(mask.astype(bool), iterations=int(smoothing))
        return mask.astype(np.uint8)

    if coords is None:
        raise ValueError("Provide image or coordinates for tissue segmentation")

    # Density-based tissue boundary: cluster high-density regions
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels = kmeans.fit_predict(coords)
    dense_cluster = np.argmax([np.sum(labels == i) for i in range(2)])
    spot_mask = (labels == dense_cluster).astype(np.uint8)
    return spot_mask


def coordinate_tissue_regions(coords: np.ndarray, n_regions: int = 3) -> np.ndarray:
    """Assign coordinate-based tissue regions via k-means."""
    kmeans = KMeans(n_clusters=n_regions, random_state=42, n_init=10)
    return kmeans.fit_predict(coords)
