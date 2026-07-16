"""Tests for mbsi.diffusion.pde_solver module (13% -> target ~80%)."""

import numpy as np

from mbsi.diffusion.pde_solver import (
    build_variable_diffusion_laplacian,
    solve_diffusion_pde,
    solve_steady_state,
)


def _isotropic_tensor_field(H, W):
    return np.tile(np.eye(2), (H, W, 1, 1))


def test_build_variable_diffusion_laplacian_shape():
    H, W = 4, 5
    tensor_field = _isotropic_tensor_field(H, W)
    L = build_variable_diffusion_laplacian(tensor_field, (H, W))
    assert L.shape == (H * W, H * W)


def test_build_variable_diffusion_laplacian_is_sparse():
    from scipy.sparse import issparse

    H, W = 3, 3
    tensor_field = _isotropic_tensor_field(H, W)
    L = build_variable_diffusion_laplacian(tensor_field, (H, W))
    assert issparse(L)


def test_laplacian_diagonal_negative():
    H, W = 4, 4
    tensor_field = _isotropic_tensor_field(H, W)
    L = build_variable_diffusion_laplacian(tensor_field, (H, W))
    diag = L.diagonal()
    assert (diag <= 0).all()


def test_solve_diffusion_pde_shape():
    H, W = 5, 5
    initial = np.zeros((H, W))
    initial[2, 2] = 1.0
    tensor_field = _isotropic_tensor_field(H, W)
    solution = solve_diffusion_pde(initial, tensor_field, dt=0.01, n_steps=5)
    assert solution.shape == (H, W)


def test_solve_diffusion_pde_diffuses():
    H, W = 5, 5
    initial = np.zeros((H, W))
    initial[2, 2] = 1.0
    tensor_field = _isotropic_tensor_field(H, W)
    solution = solve_diffusion_pde(initial, tensor_field, dt=0.01, n_steps=20)
    assert solution[2, 2] < initial[2, 2]
    assert solution.sum() > 0


def test_solve_steady_state_shape():
    H, W = 4, 4
    source = np.zeros((H, W))
    source[2, 2] = 1.0
    tensor_field = _isotropic_tensor_field(H, W)
    solution = solve_steady_state(source, tensor_field, (H, W))
    assert solution.shape == (H, W)


def test_solve_steady_state_nonzero():
    H, W = 4, 4
    source = np.ones((H, W))
    tensor_field = _isotropic_tensor_field(H, W)
    solution = solve_steady_state(source, tensor_field, (H, W))
    assert np.abs(solution).sum() > 0
