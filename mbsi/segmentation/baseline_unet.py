"""Optional baseline U-Net segmentation — local PyTorch implementation.

This module does NOT depend on the legacy zhixuhao/unet repository.
A trained weights file is required; untrained weights are rejected in production.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union

import numpy as np
from scipy import ndimage
from skimage.morphology import remove_small_objects

DEFAULT_WEIGHTS_PATH = Path("data/models/baseline_unet.pt")
UNTRAINED_MESSAGE = (
    "Untrained baseline unavailable — place trained weights at "
    "data/models/baseline_unet.pt or set MBSI_BASELINE_UNET_WEIGHTS."
)


def resolve_baseline_unet_weights_path(weights_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve baseline U-Net weights path from argument or environment."""
    if weights_path is not None:
        return Path(weights_path)
    env_path = os.environ.get("MBSI_BASELINE_UNET_WEIGHTS", "").strip()
    if env_path:
        return Path(env_path)
    return DEFAULT_WEIGHTS_PATH


def baseline_unet_weights_available(weights_path: Optional[Union[str, Path]] = None) -> bool:
    """True when a non-empty trained weights file exists."""
    path = resolve_baseline_unet_weights_path(weights_path)
    return path.is_file() and path.stat().st_size > 0


def _to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        gray = image.astype(np.float32)
    else:
        gray = np.dot(image[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)
    lo, hi = float(gray.min()), float(gray.max())
    if hi > lo:
        gray = (gray - lo) / (hi - lo)
    return gray


def _build_minimal_unet():
    """Minimal 2D U-Net for binary tissue/cell foreground (local PyTorch only)."""
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:
        raise ImportError("PyTorch is required for baseline U-Net segmentation") from exc

    class ConvBlock(nn.Module):
        def __init__(self, in_ch: int, out_ch: int):
            super().__init__()
            self.block = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
                nn.ReLU(inplace=True),
            )

        def forward(self, x):
            return self.block(x)

    class MiniUNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc1 = ConvBlock(1, 32)
            self.enc2 = ConvBlock(32, 64)
            self.pool = nn.MaxPool2d(2)
            self.bottleneck = ConvBlock(64, 128)
            self.up2 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
            self.dec2 = ConvBlock(128, 64)
            self.up1 = nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)
            self.dec1 = ConvBlock(64, 32)
            self.out = nn.Conv2d(32, 1, kernel_size=1)

        def forward(self, x):
            e1 = self.enc1(x)
            e2 = self.enc2(self.pool(e1))
            b = self.bottleneck(self.pool(e2))
            d2 = self.up2(b)
            d2 = self.dec2(torch.cat([d2, e2], dim=1))
            d1 = self.up1(d2)
            d1 = self.dec1(torch.cat([d1, e1], dim=1))
            return self.out(d1)

    return MiniUNet


def _load_model(weights_path: Path):
    import torch

    model = _build_minimal_unet()
    state = torch.load(weights_path, map_location="cpu")
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state, strict=False)
    model.eval()
    return model


def run_baseline_unet_segmentation(
    image: np.ndarray,
    *,
    weights_path: Optional[Union[str, Path]] = None,
    threshold: float = 0.5,
    min_size: int = 20,
) -> np.ndarray:
    """
    Run optional baseline U-Net on a real uploaded morphology image.

    Requires trained weights — raises RuntimeError when weights are missing.
    """
    path = resolve_baseline_unet_weights_path(weights_path)
    if not baseline_unet_weights_available(path):
        raise RuntimeError(UNTRAINED_MESSAGE)

    try:
        import torch
    except ImportError as exc:
        raise ImportError("PyTorch is required for baseline U-Net segmentation") from exc

    gray = _to_gray(image)
    tensor = torch.from_numpy(gray)[None, None, ...]
    model = _load_model(path)
    with torch.no_grad():
        logits = model(tensor)
        prob = torch.sigmoid(logits)[0, 0].cpu().numpy()

    binary = prob >= float(threshold)
    binary = remove_small_objects(binary, min_size=max(1, int(min_size)))
    labeled, _ = ndimage.label(binary)
    return labeled.astype(np.int32)
