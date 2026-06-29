"""Nuclei segmentation."""

from typing import Optional

import numpy as np
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from scipy import ndimage

from mbsi.morphology.segmentation import segment_cells


def segment_nuclei(
    image: np.ndarray,
    min_size: int = 30,
    method: str = "cellpose",
) -> np.ndarray:
    """
    Segment nuclei from tissue image.

    Returns labeled nuclei mask (H x W).
    """
    method = (method or "cellpose").lower()
    if method == "cellpose":
        from mbsi.segmentation.adapters import segment_nuclei_cellpose
        labels = segment_nuclei_cellpose(image)
        if labels is not None and labels.max() > 0:
            return labels
        method = "watershed"

    if method == "stardist":
        from mbsi.segmentation.adapters import segment_nuclei_stardist
        labels = segment_nuclei_stardist(image)
        if labels is not None and labels.max() > 0:
            return labels
        method = "watershed"

    if method == "cells":
        return segment_cells(image, min_size=min_size, method="watershed")

    if image.ndim == 3:
        gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
    else:
        gray = image.astype(np.float64)
    gray = (gray - gray.min()) / (gray.max() - gray.min() + 1e-10)

    thresh = threshold_otsu(gray)
    binary = gray > thresh
    binary = remove_small_objects(binary, min_size=min_size)
    distance = ndimage.distance_transform_edt(binary)
    coords = peak_local_max(distance, min_distance=10, labels=binary)
    markers = np.zeros_like(binary, dtype=np.int32)
    for i, (y, x) in enumerate(coords):
        markers[y, x] = i + 1
    labels = watershed(-distance, markers, mask=binary)
    return labels
