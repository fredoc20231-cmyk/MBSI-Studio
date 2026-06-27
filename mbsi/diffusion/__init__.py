"""Diffusion module for kernel computation and PDE solving."""

from mbsi.diffusion.kernel import build_diffusion_kernel
from mbsi.diffusion.green_function import compute_green_function
from mbsi.diffusion.pde_solver import solve_diffusion_pde

__all__ = ["build_diffusion_kernel", "compute_green_function", "solve_diffusion_pde"]
