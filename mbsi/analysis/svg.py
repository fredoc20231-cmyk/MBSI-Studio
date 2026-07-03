"""Spatially Variable Gene (SVG) detection with significance testing.

This module extends ``mbsi.analysis.spatial_stats`` (which provides point
estimates of Moran's I / Geary's C only) with a statistically rigorous SVG
caller:

* **Vectorized / sparse** Moran's I and Geary's C computed for *thousands* of
  genes simultaneously (replaces the per-edge Python loop in
  ``spatial_stats.gearys_c`` that is O(n_edges x n_genes)).
* **Analytic inference** for Moran's I under the normality assumption
  (Cliff & Ord z-score and two-sided p-value).
* **Permutation null** (conditional/Monte-Carlo) giving an empirical p-value
  that does not rely on distributional assumptions, for both statistics.
* **Benjamini-Hochberg FDR** correction and an ``is_svg`` call at a chosen
  q-value threshold.

The output is a tidy, ranked :class:`pandas.DataFrame` suitable for feeding the
downstream domain-detection, TME and communication modules.

References
----------
Cliff, A.D. & Ord, J.K. (1981). *Spatial Processes: Models & Applications.*
Moran, P.A.P. (1950). Notes on continuous stochastic phenomena. *Biometrika.*
The permutation scheme mirrors ``squidpy.gr.spatial_autocorr`` (a shared set of
node permutations reused across genes for efficiency; each gene's marginal null
remains an exact permutation distribution of its own values).
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from scipy import stats as _stats

from mbsi.analysis.spatial_stats import build_spatial_weights

__all__ = [
    "morans_i_vectorized",
    "gearys_c_vectorized",
    "benjamini_hochberg",
    "detect_svgs",
]


# --------------------------------------------------------------------------- #
# Matrix extraction helpers
# --------------------------------------------------------------------------- #
def _dense_matrix(adata: ad.AnnData, genes: Sequence[str], layer: str) -> np.ndarray:
    """Return an (n_obs x n_genes) dense float64 matrix for ``genes``."""
    sub = adata[:, list(genes)]
    X = sub.layers[layer] if layer in adata.layers else sub.X
    if sparse.issparse(X):
        X = X.toarray()
    return np.asarray(X, dtype=np.float64)


def _weight_moments(W: sparse.csr_matrix) -> Tuple[float, float, float]:
    """Return the weight moments S0, S1, S2 used by analytic Moran inference."""
    S0 = float(W.sum())
    # S1 = 0.5 * sum_ij (w_ij + w_ji)^2
    Wt = W.T.tocsr()
    WpWt = (W + Wt)
    S1 = 0.5 * float(WpWt.multiply(WpWt).sum())
    # S2 = sum_i (row_sum_i + col_sum_i)^2
    row_sums = np.asarray(W.sum(axis=1)).ravel()
    col_sums = np.asarray(W.sum(axis=0)).ravel()
    S2 = float(np.sum((row_sums + col_sums) ** 2))
    return S0, S1, S2


# --------------------------------------------------------------------------- #
# Vectorized statistics
# --------------------------------------------------------------------------- #
def morans_i_vectorized(X: np.ndarray, W: sparse.csr_matrix) -> np.ndarray:
    """Moran's I for every column of ``X`` at once.

    Parameters
    ----------
    X : (n_obs, n_genes) array of expression values.
    W : (n_obs, n_obs) sparse spatial weight matrix.

    Returns
    -------
    (n_genes,) array of Moran's I values.
    """
    n = X.shape[0]
    S0 = float(W.sum())
    z = X - X.mean(axis=0, keepdims=True)
    Wz = W @ z
    num = np.einsum("ij,ij->j", z, Wz)
    denom = np.einsum("ij,ij->j", z, z) + 1e-12
    return (n / S0) * (num / denom)


def gearys_c_vectorized(X: np.ndarray, W: sparse.csr_matrix) -> np.ndarray:
    """Geary's C for every column of ``X`` at once.

    Uses the identity ``sum_ij w_ij (x_i - x_j)^2 =
    sum_i (d_row_i + d_col_i) x_i^2 - 2 x^T W x`` so no per-edge loop is needed.
    """
    n = X.shape[0]
    S0 = float(W.sum())
    d = np.asarray(W.sum(axis=1)).ravel() + np.asarray(W.sum(axis=0)).ravel()
    X2 = X * X
    cross = np.einsum("ij,ij->j", X, W @ X)          # x^T W x per gene
    # sum_ij w_ij (x_i - x_j)^2 = (d_row + d_col).x^2 - 2 x^T W x
    num = (d @ X2) - 2.0 * cross
    z = X - X.mean(axis=0, keepdims=True)
    denom = np.einsum("ij,ij->j", z, z) + 1e-12
    return ((n - 1) / (2.0 * S0)) * (num / denom)


# --------------------------------------------------------------------------- #
# Analytic inference for Moran's I (normality assumption)
# --------------------------------------------------------------------------- #
def _moran_analytic_pvalues(
    I: np.ndarray, W: sparse.csr_matrix
) -> Tuple[np.ndarray, np.ndarray, float, float]:
    """Return (z_scores, two-sided p-values, E[I], Var[I]) under normality."""
    n = W.shape[0]
    S0, S1, S2 = _weight_moments(W)
    EI = -1.0 / (n - 1)
    # Variance under the normality assumption (Cliff & Ord).
    var_num = n * n * S1 - n * S2 + 3.0 * S0 * S0
    var_den = (n * n - 1.0) * S0 * S0
    VarI = var_num / var_den - EI * EI
    VarI = max(VarI, 1e-12)
    z = (I - EI) / np.sqrt(VarI)
    p = 2.0 * _stats.norm.sf(np.abs(z))
    return z, p, EI, VarI


# --------------------------------------------------------------------------- #
# Permutation null
# --------------------------------------------------------------------------- #
def _permutation_pvalues(
    X: np.ndarray,
    W: sparse.csr_matrix,
    observed: np.ndarray,
    statistic: str,
    n_perms: int,
    rng: np.random.Generator,
    two_sided: bool,
) -> Tuple[np.ndarray, np.ndarray]:
    """Empirical p-values from ``n_perms`` shared node permutations.

    Returns (p_perm, z_perm) where ``z_perm`` standardizes the observed
    statistic against the permutation mean/std.
    """
    n, g = X.shape
    func = morans_i_vectorized if statistic == "moran" else gearys_c_vectorized
    perm_stats = np.empty((n_perms, g), dtype=np.float64)
    for b in range(n_perms):
        perm = rng.permutation(n)
        perm_stats[b] = func(X[perm], W)

    mean = perm_stats.mean(axis=0)
    std = perm_stats.std(axis=0) + 1e-12
    z_perm = (observed - mean) / std

    if statistic == "moran":
        # Higher I  => more positive spatial autocorrelation (clustered).
        ge = (perm_stats >= observed[None, :]).sum(axis=0)
        le = (perm_stats <= observed[None, :]).sum(axis=0)
        if two_sided:
            tail = np.minimum(ge, le)
            p = (2.0 * tail + 1.0) / (n_perms + 1.0)
            p = np.minimum(p, 1.0)
        else:
            p = (ge + 1.0) / (n_perms + 1.0)
    else:
        # Geary's C < 1 => positive autocorrelation, so a LOW C is the signal.
        le = (perm_stats <= observed[None, :]).sum(axis=0)
        ge = (perm_stats >= observed[None, :]).sum(axis=0)
        if two_sided:
            tail = np.minimum(ge, le)
            p = (2.0 * tail + 1.0) / (n_perms + 1.0)
            p = np.minimum(p, 1.0)
        else:
            p = (le + 1.0) / (n_perms + 1.0)
    return p, z_perm


# --------------------------------------------------------------------------- #
# FDR
# --------------------------------------------------------------------------- #
def benjamini_hochberg(pvals: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg FDR-adjusted q-values."""
    p = np.asarray(pvals, dtype=float)
    n = p.size
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    # enforce monotonicity from the largest p downward
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    q = np.empty_like(ranked)
    q[order] = np.clip(ranked, 0, 1)
    return q


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def detect_svgs(
    adata: ad.AnnData,
    genes: Optional[List[str]] = None,
    layer: str = "logcounts",
    k: int = 6,
    method: str = "moran",
    n_perms: int = 100,
    two_sided: bool = False,
    fdr_alpha: float = 0.05,
    n_top: Optional[int] = 2000,
    random_state: Optional[int] = 0,
    W: Optional[sparse.csr_matrix] = None,
) -> pd.DataFrame:
    """Detect spatially variable genes with significance testing.

    Parameters
    ----------
    adata : AnnData
        Must contain ``obsm['spatial']``. Expression is read from ``layer`` if
        present, else ``.X``.
    genes : list of str, optional
        Genes to test. Defaults to highly-variable genes if flagged, else all.
    layer : str
        Expression layer to use (default ``'logcounts'``).
    k : int
        Number of spatial neighbours for the kNN weight graph.
    method : {'moran', 'geary'}
        Which statistic to use for the primary significance call.
    n_perms : int
        Number of node permutations for the empirical null (0 disables it;
        Moran then falls back to analytic p-values).
    two_sided : bool
        If True test both tails; otherwise test the positive-autocorrelation
        tail (the usual SVG hypothesis).
    fdr_alpha : float
        q-value threshold for the ``is_svg`` call.
    n_top : int, optional
        Cap on the number of genes tested (after the default HVG selection).
    random_state : int, optional
        Seed for the permutation RNG.
    W : sparse matrix, optional
        Precomputed spatial weights (skips ``build_spatial_weights``).

    Returns
    -------
    pandas.DataFrame
        Columns: ``gene``, the statistic (``morans_i``/``gearys_c``), both
        statistics when available, ``z``, ``pval``, ``pval_analytic``
        (Moran only), ``fdr``, ``is_svg``; ranked most- to least-significant.
    """
    if method not in {"moran", "geary"}:
        raise ValueError("method must be 'moran' or 'geary'")
    if "spatial" not in adata.obsm:
        raise ValueError("adata.obsm['spatial'] is required for SVG detection")

    if genes is None:
        if "highly_variable" in adata.var.columns:
            genes = adata.var_names[adata.var["highly_variable"]].tolist()
        else:
            genes = adata.var_names.tolist()
    genes = [g for g in genes if g in set(adata.var_names)]
    if n_top is not None:
        genes = genes[:n_top]
    if not genes:
        return pd.DataFrame(
            columns=["gene", "morans_i", "gearys_c", "z", "pval", "fdr", "is_svg"]
        )

    if W is None:
        W = build_spatial_weights(adata, k=k)
    X = _dense_matrix(adata, genes, layer)

    # Drop zero-variance genes (undefined statistic) but keep them in output.
    var = X.var(axis=0)
    valid = var > 1e-12

    I = np.full(len(genes), np.nan)
    C = np.full(len(genes), np.nan)
    I[valid] = morans_i_vectorized(X[:, valid], W)
    C[valid] = gearys_c_vectorized(X[:, valid], W)

    rng = np.random.default_rng(random_state)
    z = np.full(len(genes), np.nan)
    pval = np.full(len(genes), np.nan)
    p_analytic = np.full(len(genes), np.nan)

    # Analytic Moran inference (always available, cheap).
    if valid.any():
        z_a, p_a, EI, VarI = _moran_analytic_pvalues(I[valid], W)
        p_analytic[valid] = p_a
        if method == "moran":
            z[valid] = z_a
            pval[valid] = p_a

    # Permutation inference (overrides analytic p for the chosen statistic).
    if n_perms and valid.any():
        obs = I[valid] if method == "moran" else C[valid]
        p_perm, z_perm = _permutation_pvalues(
            X[:, valid], W, obs, method, n_perms, rng, two_sided
        )
        pval[valid] = p_perm
        z[valid] = z_perm

    fdr = np.full(len(genes), np.nan)
    fdr[valid] = benjamini_hochberg(pval[valid])
    is_svg = np.zeros(len(genes), dtype=bool)
    is_svg[valid] = fdr[valid] < fdr_alpha

    df = pd.DataFrame(
        {
            "gene": genes,
            "morans_i": I,
            "gearys_c": C,
            "z": z,
            "pval": pval,
            "pval_analytic": p_analytic,
            "fdr": fdr,
            "is_svg": is_svg,
        }
    )
    # Rank: significant genes first, then by |z| / statistic strength.
    sort_key = "morans_i" if method == "moran" else "gearys_c"
    ascending = method == "geary"  # low Geary's C == strong signal
    df = df.sort_values(
        ["is_svg", "fdr", sort_key], ascending=[False, True, ascending]
    ).reset_index(drop=True)
    df.attrs["method"] = method
    df.attrs["n_perms"] = n_perms
    df.attrs["k"] = k
    df.attrs["fdr_alpha"] = fdr_alpha
    return df
