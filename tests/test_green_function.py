"""Tests for mbsi.diffusion.green_function module (14% -> target ~90%)."""

import numpy as np
import pytest

from mbsi.diffusion.green_function import (
    build_variable_diffusion_laplacian,
    compute_fundamental_solution,
    compute_green_function,
)


def _isotropic_tensor_field(H, W):
    return np.tile(np.eye(2), (H, W, 1, 1))


def test_build_variable_diffusion_laplacian_shape():
    H, W = 4, 5
    tensor_field = _isotropic_tensor_field(H, W)
    L = build_variable_diffusion_laplacian(tensor_field, (H, W))
    assert L.shape == (H * W, H * W)


def test_build_variable_diffusion_laplacian_diagonal_negative():
    H, W = 3, 3
    tensor_field = _isotropic_tensor_field(H, W)
    L = build_variable_diffusion_laplacian(tensor_field, (H, W))
    diag = L.diagonal()
    assert (diag <= 0).all()


def test_compute_green_function_shape():
    H, W = 5, 5
    tensor_field = _isotropic_tensor_field(H, W)
    source = np.array([2, 2])
    green = compute_green_function(tensor_field, source, (H, W))
    assert green.shape == (H, W)


def test_compute_green_function_peak_near_source():
    H, W = 5, 5
    tensor_field = _isotropic_tensor_field(H, W)
    source = np.array([2, 2])
    green = compute_green_function(tensor_field, source, (H, W))
    assert green[2, 2] != 0


def test_compute_fundamental_solution_positive():
    tensor = np.eye(2)
    distance = 1.0
    val = compute_fundamental_solution(tensor, distance)
    assert isinstance(val, float)


def test_compute_fundamental_solution_log_decay():
    tensor = np.eye(2)
    val1 = compute_fundamental_solution(tensor, 1.0)
    val2 = compute_fundamental_solution(tensor, 2.0)
    assert val2 < val1


def test_compute_fundamental_solution_nonpositive_det():
    tensor = np.zeros((2, 2))
    with pytest.raises(ValueError, match="positive definite"):
        compute_fundamental_solution(tensor, 1.0)


def test_compute_fundamental_solution_anisotropic():
    tensor = np.array([[2.0, 0.0], [0.0, 0.5]])
    val = compute_fundamental_solution(tensor, 1.0)
    assert isinstance(val, float)
