"""Cell boundary inference and Voronoi fallbacks."""

from typing import Optional

import numpy as np
from skimage.segmentation import find_boundaries


def infer_cell_boundaries(
    image: Optional[np.ndarray] = None,
    nuclei_mask: Optional[np.ndarray] = None,
    boundary_threshold: float = 0.5,
) -> np.ndarray:
    """
    Infer cell boundaries from nuclei mask or image edges.

    Returns boundary map (same shape as input mask/image).
    """
    if nuclei_mask is not None:
        boundaries = find_boundaries(nuclei_mask, mode="outer").astype(np.uint8)
        return boundaries

    if image is not None:
        from mbsi.morphology.image_features import detect_boundaries
        return detect_boundaries(image)

    raise ValueError("Provide nuclei_mask or image for boundary inference")


def voronoi_cell_regions(coords: np.ndarray, clip_mask: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Assign Voronoi-like cell regions from spatial coordinates.

    Returns integer region label per point (n_points,).
    """
    from mbsi.segmentation.cells import generate_voronoi_cells
    return generate_voronoi_cells(coords, clip_mask=clip_mask)
