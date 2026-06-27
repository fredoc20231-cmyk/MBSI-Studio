"""Tissue segmentation from H&E or coordinate-based fallback."""

from typing import Optional

import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d
from sklearn.cluster import KMeans

from mbsi.morphology.image_features import compute_tissue_mask


def segment_tissue(
    image: Optional[np.ndarray] = None,
    coords: Optional[np.ndarray] = None,
    smoothing: float = 1.0,
    min_size: int = 100,
) -> np.ndarray:
    """
    Segment tissue mask from image or density-based fallback on coordinates.

    Returns binary tissue mask (H x W) or region labels per spot/cell index.
    """
    if image is not None:
        mask = compute_tissue_mask(image)
        if smoothing > 1.0:
            from scipy import ndimage
            mask = ndimage.binary_opening(mask, iterations=int(smoothing))
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
