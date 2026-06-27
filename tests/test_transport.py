"""
Tests for optimal transport module.
"""

import pytest
import numpy as np


def test_solve_unbalanced_ot():
    """Test unbalanced optimal transport."""
    from mbsi.transport.unbalanced_ot import solve_unbalanced_ot
    
    # Create test distributions
    n = 10
    m = 15
    a = np.random.rand(n)
    b = np.random.rand(m)
    cost = np.random.rand(n, m)
    
    # Solve OT
    transport_plan, log = solve_unbalanced_ot(a, b, cost, epsilon=0.1, max_iter=100)
    
    # Check shape
    assert transport_plan.shape == (n, m)
    
    # Check non-negativity
    assert np.all(transport_plan >= 0)
    
    # Check log contains expected keys
    assert 'objective' in log
    assert 'iterations' in log
    assert 'converged' in log


def test_sinkhorn():
    """Test Sinkhorn algorithm."""
    from mbsi.transport.sinkhorn import sinkhorn
    
    n = 10
    m = 10
    a = np.random.rand(n)
    b = np.random.rand(m)
    cost = np.random.rand(n, m)
    
    transport_plan, log = sinkhorn(a, b, cost, epsilon=0.1, max_iter=100, log=True)
    
    assert transport_plan.shape == (n, m)
    assert np.all(transport_plan >= 0)
    assert log is not None
    assert 'iterations' in log


def test_ot_convergence():
    """Test OT convergence with simple case."""
    from mbsi.transport.unbalanced_ot import solve_unbalanced_ot
    
    # Simple case: uniform distributions
    n = 5
    a = np.ones(n) / n
    b = np.ones(n) / n
    cost = np.random.rand(n, n)
    
    transport_plan, log = solve_unbalanced_ot(a, b, cost, epsilon=0.1, max_iter=200)
    
    # Should converge
    assert log['converged'] == True
