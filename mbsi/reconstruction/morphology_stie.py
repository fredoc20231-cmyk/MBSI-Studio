"""Experimental morphology-guided spot deconvolution.

Not a reproduction of published STIE or evidence of single-cell ground truth.
Input expression and signatures must be nonnegative, in identical gene order.
Nuclear coordinates must be measured and registered to spot coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.spatial import cKDTree
from scipy.special import logsumexp


@dataclass
class STIEResult:
    spot_abundance: np.ndarray
    cell_probabilities: np.ndarray
    cell_type_index: np.ndarray
    cell_confidence: np.ndarray
    morphology_means: np.ndarray
    morphology_variances: np.ndarray
    objective_history: list[float]
    converged: bool
    cell_to_spot: np.ndarray


def _matrix(name, value, *, nonnegative=False):
    a = np.asarray(value, dtype=np.float64)
    if a.ndim != 2 or not a.size or not np.all(np.isfinite(a)):
        raise ValueError(f"{name} must be a nonempty finite 2D matrix")
    if nonnegative and np.any(a < 0):
        raise ValueError(f"{name} must be nonnegative")
    return a


def _objective(E, G, A, P, penalty):
    residual = E - A @ G.T
    B = np.eye(A.shape[1]) - np.ones((A.shape[1], 1)) @ P[None, :]
    # P is per spot; evaluate separately below instead.
    return 0.5 * np.sum(residual**2) + 0.5 * penalty * np.sum(
        (A - A.sum(axis=1, keepdims=True) * P)**2
    )


def _fista(E, G, P, start, penalty, max_iter, tol):
    """Projected accelerated gradient with monotone restart and exact gradient."""
    n_types = G.shape[1]
    eye = np.eye(n_types)
    gram = G.T @ G
    cross = E @ G
    # Each spot has its own Hessian; global upper bound gives safe steps.
    L = float(np.linalg.eigvalsh(gram).max())
    for p in P:
        B = eye - np.ones((n_types, 1)) @ p[None, :]
        L = max(L, float(np.linalg.eigvalsh(gram + penalty * (B @ B.T)).max()))
    if L <= 0:
        raise ValueError("Unidentifiable optimization: zero signatures and penalty")
    A = start.copy()
    y = A.copy()
    t = 1.0
    previous = _objective(E, G, A, P, penalty)
    for _ in range(max_iter):
        total = y.sum(axis=1, keepdims=True)
        R = y - total * P
        # derivative of ||a - (sum a)p||² = 2 R (I - 1 p^T)^T
        gradient = y @ gram - cross + penalty * (R - (R * P).sum(axis=1, keepdims=True))
        candidate = np.maximum(0, y - gradient / L)
        value = _objective(E, G, candidate, P, penalty)
        if value > previous + 1e-10 * max(1.0, previous):
            y, t = A.copy(), 1.0
            total = y.sum(axis=1, keepdims=True)
            R = y - total * P
            gradient = y @ gram - cross + penalty * (R - (R * P).sum(axis=1, keepdims=True))
            candidate = np.maximum(0, y - gradient / L)
            value = _objective(E, G, candidate, P, penalty)
        if np.linalg.norm(candidate - A) <= tol * max(1.0, np.linalg.norm(A)):
            return candidate
        next_t = (1 + np.sqrt(1 + 4 * t*t)) / 2
        y = candidate + (t - 1) / next_t * (candidate - A)
        A, t, previous = candidate, next_t, value
    return A


def fit_morphology_stie(
    expression, signatures, morphology, cell_coords, spot_coords, *,
    penalty=1.0, em_iters=40, fista_iters=200, ridge=1e-4,
    tol=1e-5, random_state=0, max_assignment_distance=None,
):
    """Fit a constrained experimental model; all spatial distances in same units.

    Cells are assigned to their nearest observed spot, not synthesized. Optionally
    reject cells beyond a measured max_assignment_distance. Returns probabilities
    and uncertainty; does not invent cells in unobserved gaps.
    """
    E = _matrix("expression", expression, nonnegative=True)
    G = _matrix("signatures", signatures, nonnegative=True)
    M = _matrix("morphology", morphology)
    cells = _matrix("cell_coords", cell_coords)
    spots = _matrix("spot_coords", spot_coords)
    if E.shape[1] != G.shape[0] or cells.shape != (M.shape[0], 2) or spots.shape != (E.shape[0], 2):
        raise ValueError("Incompatible expression/signature/morphology/spatial dimensions")
    if not np.any(G > 0) or np.any(np.sum(G, axis=0) == 0):
        raise ValueError("Every signature must have at least one positive feature")
    if not np.isfinite(penalty) or penalty < 0 or not np.isfinite(ridge) or ridge <= 0:
        raise ValueError("penalty must be >= 0 and ridge must be > 0")
    if em_iters < 1 or fista_iters < 1 or not (0 < tol < 1):
        raise ValueError("Invalid iteration count or tolerance")
    distances, assignment = cKDTree(spots).query(cells)
    if max_assignment_distance is not None:
        if max_assignment_distance <= 0 or np.any(distances > max_assignment_distance):
            raise ValueError("Cells outside registered spot-assignment radius")
    n_spots, n_types = E.shape[0], G.shape[1]
    rng = np.random.default_rng(random_state)
    A = np.maximum(E @ G @ np.linalg.pinv(G.T @ G + ridge * np.eye(n_types)), ridge)
    # Randomized morphology initialization is reproducible with the supplied seed.
    mu = M[rng.choice(M.shape[0], n_types, replace=M.shape[0] < n_types)].copy()
    var = np.maximum(np.var(M, axis=0, keepdims=True), ridge).repeat(n_types, axis=0)
    history = []
    converged = False
    W = np.full((len(M), n_types), 1 / n_types)
    for _ in range(em_iters):
        prior = A / np.maximum(A.sum(axis=1, keepdims=True), ridge)
        log_likelihood = -0.5 * (
            ((M[:, None, :] - mu[None, :, :])**2 / var[None, :, :]).sum(axis=2)
            + np.log(var).sum(axis=1)[None, :]
        )
        log_w = log_likelihood + np.log(np.maximum(prior[assignment], 1e-12))
        W = np.exp(log_w - logsumexp(log_w, axis=1, keepdims=True))
        weights = np.maximum(W.sum(axis=0), ridge)
        mu = (W.T @ M) / weights[:, None]
        var = np.maximum(
            np.einsum("ct,ctf->tf", W, (M[:, None, :] - mu[None, :, :])**2) / weights[:, None],
            ridge,
        )
        P = np.zeros((n_spots, n_types))
        np.add.at(P, assignment, W)
        counts = np.bincount(assignment, minlength=n_spots)
        nonempty = counts > 0
        P[nonempty] /= counts[nonempty, None]
        P[~nonempty] = prior[~nonempty]  # no fabricated morphology evidence
        A_new = _fista(E, G, P, A, penalty, fista_iters, tol)
        obj = _objective(E, G, A_new, P, penalty)
        history.append(float(obj))
        if np.linalg.norm(A_new - A) <= tol * max(1.0, np.linalg.norm(A)):
            converged = True
            A = A_new
            break
        A = A_new
    # Recompute final posteriors with the final fitted parameters.
    prior = A / np.maximum(A.sum(axis=1, keepdims=True), ridge)
    log_likelihood = -0.5 * (
        ((M[:, None, :] - mu[None, :, :])**2 / var[None, :, :]).sum(axis=2)
        + np.log(var).sum(axis=1)[None, :]
    )
    log_w = log_likelihood + np.log(np.maximum(prior[assignment], 1e-12))
    W = np.exp(log_w - logsumexp(log_w, axis=1, keepdims=True))
    return STIEResult(A, W, W.argmax(axis=1), W.max(axis=1), mu, var, history, converged, assignment)
