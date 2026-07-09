"""StarDist nuclei segmentation and expansion to cell boundaries."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple, Union

import numpy as np
from scipy import ndimage
from skimage.segmentation import watershed


def _extract_channel(image: np.ndarray, channel: Optional[Union[int, str]]) -> np.ndarray:
    if image.ndim == 2:
        return image.astype(np.float64)
    if channel is None or channel == "grayscale":
        return np.dot(image[..., :3], [0.299, 0.587, 0.114]).astype(np.float64)
    channel_map = {"red": 0, "green": 1, "blue": 2, "dapi": 0}
    if isinstance(channel, str):
        key = channel.lower()
        if key in channel_map:
            idx = channel_map[key]
            return image[..., min(idx, image.shape[-1] - 1)].astype(np.float64)
        raise ValueError(f"Unknown channel: {channel}")
    return image[..., int(channel)].astype(np.float64)


def run_stardist_nuclei_segmentation(
    image: np.ndarray,
    model_name: str = "2D_versatile_fluo",
    n_tiles: Tuple[int, int] = (2, 2),
    channel: Optional[Union[int, str]] = None,
) -> np.ndarray:
    """Run StarDist 2D nuclei segmentation on a real morphology image."""
    try:
        from csbdeep.utils import normalize
        from stardist.models import StarDist2D
    except ImportError as exc:
        raise ImportError(
            "StarDist is not installed. Install with: pip install stardist tensorflow"
        ) from exc

    gray = _extract_channel(image, channel)
    model = StarDist2D.from_pretrained(model_name)
    labels, _ = model.predict_instances(normalize(gray), n_tiles=n_tiles)
    return labels.astype(np.int32)


def expand_nuclei_to_cells(nuclear_mask: np.ndarray, expansion_pixels: int = 5) -> np.ndarray:
    """Expand labeled nuclei masks into approximate cell boundaries via constrained watershed."""
    nuclear_mask = np.asarray(nuclear_mask, dtype=np.int32)
    if nuclear_mask.max() == 0:
        return nuclear_mask.copy()

    expansion_pixels = max(1, int(expansion_pixels))
    background = nuclear_mask == 0
    distance = ndimage.distance_transform_edt(background)
    allowed = (distance <= expansion_pixels) | (nuclear_mask > 0)
    expanded = watershed(
        distance,
        markers=nuclear_mask,
        mask=allowed,
    )
    return expanded.astype(np.int32)
