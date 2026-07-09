"""DeepCell Mesmer segmentation pipeline (optional)."""

from __future__ import annotations

from typing import Literal, Optional, Union

import numpy as np


Compartment = Literal["whole-cell", "nuclear"]


def mesmer_available() -> bool:
    try:
        from deepcell.applications import Mesmer  # noqa: F401
        return True
    except ImportError:
        return False


def _prepare_mesmer_input(image: np.ndarray) -> np.ndarray:
    """Mesmer expects (batch, H, W, 2) with nuclear + membrane channels."""
    if image.ndim == 2:
        ch = image.astype(np.float32)
        if ch.max() > 1:
            ch = ch / 255.0
        pair = np.stack([ch, ch], axis=-1)
    elif image.ndim == 3:
        arr = image.astype(np.float32)
        if arr.max() > 1:
            arr = arr / 255.0
        if arr.shape[-1] >= 2:
            pair = arr[..., :2]
        else:
            ch = arr[..., 0]
            pair = np.stack([ch, ch], axis=-1)
    else:
        raise ValueError("Mesmer expects a 2D or HxWxC morphology image")
    return pair[np.newaxis, ...]


def run_mesmer_segmentation(
    image: np.ndarray,
    compartment: Compartment = "whole-cell",
    *,
    image_mpp: float = 0.5,
) -> np.ndarray:
    """
    Run DeepCell Mesmer on a real morphology image.

    Requires: pip install deepcell
    """
    try:
        from deepcell.applications import Mesmer
    except ImportError as exc:
        raise ImportError(
            "DeepCell Mesmer is not installed. Install with: pip install deepcell"
        ) from exc

    batch = _prepare_mesmer_input(image)
    app = Mesmer()
    labels = app.predict(batch, compartment=compartment, image_mpp=image_mpp)
    labels = np.squeeze(labels)
    if labels.ndim > 2:
        labels = labels[0]
    return labels.astype(np.int32)
