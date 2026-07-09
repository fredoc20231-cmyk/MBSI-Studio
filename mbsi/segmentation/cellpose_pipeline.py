"""Cellpose segmentation pipeline."""

from __future__ import annotations

from typing import List, Optional, Union

import numpy as np


def _extract_channel(image: np.ndarray, channels: List[int]) -> np.ndarray:
    if image.ndim == 2:
        return image.astype(np.float64)
    if len(channels) >= 2 and channels[0] == channels[1]:
        idx = channels[0]
        if idx < image.shape[-1]:
            return image[..., idx].astype(np.float64)
    return np.dot(image[..., :3], [0.299, 0.587, 0.114]).astype(np.float64)


def run_cellpose_segmentation(
    image: np.ndarray,
    model_type: str = "nuclei",
    diameter: Optional[float] = None,
    channels: Optional[List[int]] = None,
    gpu: bool = False,
) -> np.ndarray:
    """Run Cellpose or Omnipose-compatible segmentation on a real morphology image."""
    try:
        from cellpose import models
    except ImportError as exc:
        raise ImportError(
            "Cellpose is not installed. Install with: pip install cellpose"
        ) from exc

    channels = channels if channels is not None else [0, 0]
    gray = _extract_channel(image, channels)
    model = models.Cellpose(model_type=model_type, gpu=gpu)
    masks, _, _, _ = model.eval(gray, diameter=diameter, channels=channels)
    return masks.astype(np.int32)
