"""Tests for spatial registration."""

import numpy as np

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.segmentation import (
    apply_transform_to_coords,
    estimate_affine_transform,
    register_spatial_to_image,
    validate_registration,
)
from mbsi.segmentation.tissue import segment_tissue


def _synthetic_he():
    rng = np.random.default_rng(1)
    img = rng.integers(180, 240, (64, 64, 3), dtype=np.uint8)
    img[8:56, 8:56] = rng.integers(60, 140, (48, 48, 3), dtype=np.uint8)
    return img


def test_estimate_affine_transform():
    src = np.array([[0, 0], [1, 0], [0, 1]], dtype=float)
    tgt = np.array([[0, 0], [2, 0], [0, 2]], dtype=float)
    t = estimate_affine_transform(src, tgt)
    assert t.shape == (3, 3)
    mapped = apply_transform_to_coords(src, t)
    np.testing.assert_allclose(mapped, tgt, atol=1e-6)


def test_register_spatial_to_image():
    adata = make_synthetic_visium_adata(n_spots=50)
    image = _synthetic_he()
    result = register_spatial_to_image(adata, image=image)
    assert result["status"] == "ok"
    assert "spatial_registered" in adata.obsm


def test_validate_registration():
    adata = make_synthetic_visium_adata(n_spots=40)
    image = _synthetic_he()
    register_spatial_to_image(adata, image=image)
    tissue = segment_tissue(image=image, method="otsu")
    validation = validate_registration(adata, tissue)
    assert "fraction_in_tissue" in validation
    assert "valid" in validation
