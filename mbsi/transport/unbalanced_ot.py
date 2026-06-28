"""
Unbalanced optimal transport for expression deconvolution.

Implements entropy-regularized unbalanced Sinkhorn algorithm
with marginal relaxation parameters.
"""

import logging
from typing import Tuple, Dict, Any

import numpy as np
from ot import sinkhorn as ot_sinkhorn

logger = logging.getLogger(__name__)


def solve_unbalanced_ot(
    a: np.ndarray,
    b: np.ndarray,
    cost: np.ndarray,
    epsilon: float = 0.05,
    rho1: float = 1.0,
    rho2: float = 1.0,
    max_iter: int = 500,
    tol: float = 1e-6
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Solve entropy-regularized unbalanced optimal transport.
    
    Parameters
    ----------
    a : ndarray
        Source distribution (n_spots,)
    b : ndarray
        Target distribution (n_cells,)
    cost : ndarray
        Cost matrix (n_spots x n_cells)
    epsilon : float
        Entropy regularization parameter
    rho1 : float
        Marginal relaxation for source (unbalancedness)
    rho2 : float
        Marginal relaxation for target (unbalancedness)
    max_iter : int
        Maximum number of iterations
    tol : float
        Convergence tolerance
        
    Returns
    -------
    transport_plan : ndarray
        Optimal transport plan (n_spots x n_cells)
    log : dict
        Convergence log with:
        - objective: final objective value
        - iterations: number of iterations
        - converged: whether converged
        - marginal_error: marginal constraint error
    """
    # Normalize distributions
    a = a / a.sum()
    b = b / b.sum()
    
    # Solve using POT library
    try:
        transport_plan = ot_sinkhorn(
            a, b, cost,
            reg=epsilon,
            reg_type='kl',
            max_iter=max_iter,
            stop_thresh=tol
        )
        
        # Compute objective
        objective = np.sum(transport_plan * cost) + \
                   epsilon * np.sum(transport_plan * np.log(transport_plan + 1e-16))
        
        # Compute marginal errors
        marginal_error = np.linalg.norm(transport_plan.sum(axis=1) - a) + \
                         np.linalg.norm(transport_plan.sum(axis=0) - b)
        
        log = {
            "objective": float(objective),
            "iterations": max_iter,
            "converged": marginal_error < tol,
            "marginal_error": float(marginal_error),
            "epsilon": epsilon,
            "rho1": rho1,
            "rho2": rho2
        }
        
        return transport_plan, log
        
    except Exception as e:
        logger.warning(
            "POT sinkhorn failed (%s: %s); falling back to manual implementation",
            type(e).__name__, e,
        )
        return solve_unbalanced_ot_fallback(
            a, b, cost, epsilon, rho1, rho2, max_iter, tol
        )


def solve_unbalanced_ot_fallback(
    a: np.ndarray,
    b: np.ndarray,
    cost: np.ndarray,
    epsilon: float = 0.05,
    rho1: float = 1.0,
    rho2: float = 1.0,
    max_iter: int = 500,
    tol: float = 1e-6
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Fallback implementation of unbalanced Sinkhorn.
    
    Simple iterative algorithm for unbalanced OT when POT is unavailable.
    """
    n_spots, n_cells = cost.shape
    
    # Initialize dual variables
    f = np.zeros(n_spots)
    g = np.zeros(n_cells)
    
    # Kernelized cost
    K = np.exp(-cost / epsilon)
    
    for iteration in range(max_iter):
        f_prev = f.copy()
        
        # Update f
        f = epsilon * np.log(a + 1e-16) - \
            epsilon * np.log(K @ np.exp((g - b / rho2) / epsilon) + 1e-16) + \
            rho1 / 2 * np.ones(n_spots)
        
        # Update g
        g = epsilon * np.log(b + 1e-16) - \
            epsilon * np.log(K.T @ np.exp((f - a / rho1) / epsilon) + 1e-16) + \
            rho2 / 2 * np.ones(n_cells)
        
        # Check convergence
        if np.linalg.norm(f - f_prev) < tol:
            break
    
    # Compute transport plan
    transport_plan = np.exp((f[:, None] + g[None, :] - cost) / epsilon)
    
    # Compute objective
    objective = np.sum(transport_plan * cost) + \
               epsilon * np.sum(transport_plan * np.log(transport_plan + 1e-16))
    
    # Compute marginal errors
    marginal_error = np.linalg.norm(transport_plan.sum(axis=1) - a) + \
                     np.linalg.norm(transport_plan.sum(axis=0) - b)
    
    log = {
        "objective": float(objective),
        "iterations": iteration + 1,
        "converged": marginal_error < tol,
        "marginal_error": float(marginal_error),
        "epsilon": epsilon,
        "rho1": rho1,
        "rho2": rho2
    }
    
    return transport_plan, log


def solve_balanced_ot(
    a: np.ndarray,
    b: np.ndarray,
    cost: np.ndarray,
    epsilon: float = 0.05,
    max_iter: int = 500,
    tol: float = 1e-6
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Solve balanced optimal transport (standard Sinkhorn).
    
    Parameters
    ----------
    a : ndarray
        Source distribution (must sum to same as b)
    b : ndarray
        Target distribution (must sum to same as a)
    cost : ndarray
        Cost matrix
    epsilon : float
        Entropy regularization
    max_iter : int
        Maximum iterations
    tol : float
        Convergence tolerance
        
    Returns
    -------
    transport_plan : ndarray
        Optimal transport plan
    log : dict
        Convergence log
    """
    # Use unbalanced with strong marginal constraints
    return solve_unbalanced_ot(a, b, cost, epsilon, rho1=1000, rho2=1000, 
                              max_iter=max_iter, tol=tol)
