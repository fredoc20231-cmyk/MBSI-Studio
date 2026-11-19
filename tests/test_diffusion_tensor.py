"""Tests for mbsi.morphology.diffusion_tensor module (13% -> target ~80%)."""

import numpy as np

from mbsi.morphology.diffusion_tensor import (
    build_tensor_field,
    estimate_diffusion_tensor,
    tensor_distance,
)


def test_estimate_diffusion_tensor_shape():
    H, W, F = 6, 6, 3
    features = np.random.RandomState(42).rand(H, W, F).astype(np.float32)
    tensors = estimate_diffusion_tensor(features)
    assert tensors.shape == (H, W, 2, 2)


def test_estimate_diffusion_tensor_symmetric():
    H, W, F = 5, 5, 2
    features = np.random.RandomState(0).rand(H, W, F).astype(np.float32)
    tensors = estimate_diffusion_tensor(features)
    for i in range(H):
        for j in range(W):
            np.testing.assert_allclose(tensors[i, j], tensors[i, j].T, atol=1e-10)


def test_estimate_diffusion_tensor_positive_definite():
    H, W, F = 4, 4, 2
    features = np.random.RandomState(1).rand(H, W, F).astype(np.float32)
    tensors = estimate_diffusion_tensor(features, min_eigenvalue=0.1)
    for i in range(H):
        for j in range(W):
            eigvals = np.linalg.eigvalsh(tensors[i, j])
            assert (eigvals > 0).all(), f"Non-positive eigenvalue at ({i},{j})"


def test_estimate_diffusion_tensor_anisotropy_strength():
    H, W, F = 4, 4, 2
    features = np.random.RandomState(2).rand(H, W, F).astype(np.float32) * 10
    t_low = estimate_diffusion_tensor(features, anisotropy_strength=0.5)
    t_high = estimate_diffusion_tensor(features, anisotropy_strength=2.0)
    assert t_low.shape == t_high.shape


def test_build_tensor_field_isotropic():
    coords = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    tensors = build_tensor_field(coords, image=None, isotropic=True)
    assert tensors.shape == (3, 2, 2)
    for i in range(3):
        np.testing.assert_allclose(tensors[i], np.eye(2))


def test_build_tensor_field_no_image():
    coords = np.array([[0.0, 0.0], [1.0, 1.0]])
    tensors = build_tensor_field(coords, image=None)
    assert tensors.shape == (2, 2, 2)
    np.testing.assert_allclose(tensors[0], np.eye(2))


def test_build_tensor_field_with_image():
    coords = np.array([[0.0, 0.0], [5.0, 5.0], [9.0, 9.0]])
    image = np.random.RandomState(0).randint(0, 256, (10, 10, 3)).astype(np.uint8)
    tensors = build_tensor_field(coords, image=image)
    assert tensors.shape == (3, 2, 2)


def test_tensor_distance_identity():
    x1 = np.array([0.0, 0.0])
    x2 = np.array([1.0, 0.0])
    tensor = np.eye(2)
    dist = tensor_distance(x1, x2, tensor)
    np.testing.assert_allclose(dist, 1.0, atol=1e-10)


def test_tensor_distance_symmetric():
    rng = np.random.RandomState(42)
    x1 = rng.rand(2)
    x2 = rng.rand(2)
    tensor = np.eye(2) * 2.0
    d1 = tensor_distance(x1, x2, tensor)
    d2 = tensor_distance(x2, x1, tensor)
    np.testing.assert_allclose(d1, d2, atol=1e-10)


def test_tensor_distance_zero_for_same_point():
    x = np.array([1.0, 2.0])
    tensor = np.eye(2) * 3.0
    dist = tensor_distance(x, x, tensor)
    np.testing.assert_allclose(dist, 0.0, atol=1e-10)
