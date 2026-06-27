"""
Sinkhorn algorithm implementations for optimal transport.

Provides both balanced and unbalanced variants with various
regularization options.
"""

from typing import Optional, Tuple

import numpy as np


def sinkhorn(
    a: np.ndarray,
    b: np.ndarray,
    cost: np.ndarray,
    epsilon: float = 0.05,
    max_iter: int = 1000,
    tol: float = 1e-6,
    log: bool = False
) -> Tuple[np.ndarray, Optional[dict]]:
    """
    Balanced Sinkhorn algorithm for optimal transport.
    
    Parameters
    ----------
    a : ndarray
        Source distribution (n,)
    b : ndarray
        Target distribution (m,)
    cost : ndarray
        Cost matrix (n x m)
    epsilon : float
        Entropy regularization parameter
    max_iter : int
        Maximum number of iterations
    tol : float
        Convergence tolerance
    log : bool
        If True, return convergence log
        
    Returns
    -------
    transport_plan : ndarray
        Optimal transport plan (n x m)
    log_dict : dict, optional
        Convergence information if log=True
    """
    n, m = cost.shape
    
    # Normalize distributions
    a = a / a.sum()
    b = b / b.sum()
    
    # Kernelized cost matrix
    K = np.exp(-cost / epsilon)
    
    # Initialize scaling variables
    u = np.ones(n) / n
    v = np.ones(m) / m
    
    for iteration in range(max_iter):
        u_prev = u.copy()
        
        # Update v
        v = b / (K.T @ u)
        
        # Update u
        u = a / (K @ v)
        
        # Check convergence
        if np.linalg.norm(u - u_prev) < tol:
            break
    
    # Compute transport plan
    transport_plan = np.diag(u) @ K @ np.diag(v)
    
    if log:
        log_dict = {
            "iterations": iteration + 1,
            "converged": iteration < max_iter - 1,
            "final_error": float(np.linalg.norm(u - u_prev))
        }
        return transport_plan, log_dict
    
    return transport_plan, None


def sinkhorn_unbalanced(
    a: np.ndarray,
    b: np.ndarray,
    cost: np.ndarray,
    epsilon: float = 0.05,
    rho1: float = 1.0,
    rho2: float = 1.0,
    max_iter: int = 1000,
    tol: float = 1e-6
) -> Tuple[np.ndarray, dict]:
    """
    Unbalanced Sinkhorn algorithm with KL divergence regularization.
    
    Parameters
    ----------
    a : ndarray
        Source distribution (n,)
    b : ndarray
        Target distribution (m,)
    cost : ndarray
        Cost matrix (n x m)
    epsilon : float
        Entropy regularization
    rho1 : float
        Source marginal relaxation
    rho2 : float
        Target marginal relaxation
    max_iter : int
        Maximum iterations
    tol : float
        Convergence tolerance
        
    Returns
    -------
    transport_plan : ndarray
        Optimal transport plan (n x m)
    log : dict
        Convergence information
    """
    n, m = cost.shape
    
    # Kernelized cost
    K = np.exp(-cost / epsilon)
    
    # Initialize dual variables
    f = np.zeros(n)
    g = np.zeros(m)
    
    for iteration in range(max_iter):
        f_prev = f.copy()
        
        # Update f
        f = epsilon * np.log(a + 1e-16) - \
            epsilon * np.log(K @ np.exp((g - b / rho2) / epsilon) + 1e-16) + \
            rho1 / 2
        
        # Update g
        g = epsilon * np.log(b + 1e-16) - \
            epsilon * np.log(K.T @ np.exp((f - a / rho1) / epsilon) + 1e-16) + \
            rho2 / 2
        
        # Check convergence
        if np.linalg.norm(f - f_prev) < tol:
            break
    
    # Compute transport plan
    transport_plan = np.exp((f[:, None] + g[None, :] - cost) / epsilon)
    
    log = {
        "iterations": iteration + 1,
        "converged": iteration < max_iter - 1,
        "final_error": float(np.linalg.norm(f - f_prev))
    }
    
    return transport_plan, log


def sinkhorn_epsilon_scaling(
    a: np.ndarray,
    b: np.ndarray,
    cost: np.ndarray,
    epsilon: float = 0.05,
    n_scales: int = 5,
    max_iter_per_scale: int = 100,
    tol: float = 1e-6
) -> np.ndarray:
    """
    Sinkhorn with epsilon scaling for better convergence.
    
    Parameters
    ----------
    a : ndarray
        Source distribution
    b : ndarray
        Target distribution
    cost : ndarray
        Cost matrix
    epsilon : float
        Final epsilon value
    n_scales : int
        Number of scaling steps
    max_iter_per_scale : int
        Iterations per scale
    tol : float
        Convergence tolerance
        
    Returns
    -------
    transport_plan : ndarray
        Optimal transport plan
    """
    # Geometric progression of epsilon values
    epsilons = np.geomspace(epsilon * 10, epsilon, n_scales)
    
    transport_plan = None
    
    for eps in epsilons:
        transport_plan, _ = sinkhorn(a, b, cost, eps, max_iter_per_scale, tol)
    
    return transport_plan
