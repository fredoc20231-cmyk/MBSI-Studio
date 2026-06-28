"""Tests for mbsi.morphology.image_features module (17% -> target ~90%)."""

import numpy as np

from mbsi.morphology.image_features import (
    compute_morphology_features,
    compute_tissue_mask,
    detect_boundaries,
)


def _make_rgb_image(H=32, W=32, seed=0):
    return np.random.RandomState(seed).randint(0, 256, (H, W, 3)).astype(np.uint8)


def _make_gray_image(H=32, W=32, seed=0):
    return np.random.RandomState(seed).randint(0, 256, (H, W)).astype(np.uint8)


def test_compute_morphology_features_rgb():
    img = _make_rgb_image()
    features = compute_morphology_features(img)
    assert features.ndim == 3
    assert features.shape[:2] == img.shape[:2]
    assert features.shape[2] == 5


def test_compute_morphology_features_grayscale():
    img = _make_gray_image()
    features = compute_morphology_features(img)
    assert features.ndim == 3
    assert features.shape[:2] == img.shape


def test_compute_morphology_features_rgba():
    rng = np.random.RandomState(0)
    img = rng.randint(0, 256, (20, 20, 4)).astype(np.uint8)
    features = compute_morphology_features(img)
    assert features.shape[:2] == (20, 20)


def test_compute_morphology_features_single_channel():
    rng = np.random.RandomState(0)
    img = rng.randint(0, 256, (20, 20, 1)).astype(np.uint8)
    features = compute_morphology_features(img)
    assert features.shape[:2] == (20, 20)


def test_compute_tissue_mask_rgb():
    img = _make_rgb_image()
    mask = compute_tissue_mask(img)
    assert mask.shape == img.shape[:2]
    assert mask.dtype == np.uint8
    assert set(np.unique(mask)).issubset({0, 1})


def test_compute_tissue_mask_grayscale():
    img = _make_gray_image()
    mask = compute_tissue_mask(img)
    assert mask.shape == img.shape


def test_compute_tissue_mask_custom_threshold():
    img = _make_gray_image()
    mask = compute_tissue_mask(img, threshold=128)
    assert mask.shape == img.shape


def test_detect_boundaries_rgb():
    img = _make_rgb_image()
    boundaries = detect_boundaries(img)
    assert boundaries.shape == img.shape[:2]
    assert boundaries.min() >= 0
    assert boundaries.max() <= 1


def test_detect_boundaries_grayscale():
    img = _make_gray_image().astype(np.float64)
    boundaries = detect_boundaries(img)
    assert boundaries.shape == img.shape


def test_detect_boundaries_sigma():
    img = _make_gray_image().astype(np.float64)
    b1 = detect_boundaries(img, sigma=0.5)
    b2 = detect_boundaries(img, sigma=2.0)
    assert b1.shape == b2.shape
