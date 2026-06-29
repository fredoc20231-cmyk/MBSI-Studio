"""Tests for tissue segmentation."""

import numpy as np

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.segmentation import segment_tissue


def _synthetic_he():
    rng = np.random.default_rng(0)
    img = rng.integers(180, 240, (64, 64, 3), dtype=np.uint8)
    img[10:50, 10:50] = rng.integers(60, 140, (40, 40, 3), dtype=np.uint8)
    return img


def test_segment_tissue_otsu_image():
    mask = segment_tissue(image=_synthetic_he(), method="otsu")
    assert mask.ndim == 2
    assert mask.shape == (64, 64)
    assert mask.max() <= 1


def test_segment_tissue_coords_fallback():
    coords = np.random.randn(30, 2)
    mask = segment_tissue(coords=coords)
    assert len(mask) == 30


def test_segment_tissue_adaptive():
    mask = segment_tissue(image=_synthetic_he(), method="adaptive")
    assert mask.shape == (64, 64)


def test_tissue_with_adata_coords():
    adata = make_synthetic_visium_adata(n_spots=40)
    mask = segment_tissue(coords=adata.obsm["spatial"])
    assert len(mask) == adata.n_obs
