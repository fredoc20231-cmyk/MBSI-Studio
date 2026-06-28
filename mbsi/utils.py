"""Shared utilities used across MBSI modules.

Consolidates common patterns such as sparse-to-dense conversion,
kNN spatial graph construction, gene signature scoring,
score normalization, and AnnData result construction.
"""

from __future__ import annotations

from typing import List, Union

import anndata as ad
import numpy as np
from scipy import sparse


def to_dense_array(X: Union[np.ndarray, sparse.spmatrix]) -> np.ndarray:
    """Convert a possibly-sparse matrix to a dense numpy array."""
    if hasattr(X, "toarray"):
        return np.asarray(X.toarray(), dtype=float)
    return np.asarray(X, dtype=float)


def to_dense_flat(X: Union[np.ndarray, sparse.spmatrix]) -> np.ndarray:
    """Convert a possibly-sparse matrix to a dense 1-D numpy array."""
    if hasattr(X, "toarray"):
        return np.asarray(X.toarray(), dtype=float).flatten()
    return np.asarray(X, dtype=float).flatten()


def build_knn_graph(
    coords: np.ndarray,
    k: int,
    *,
    include_self: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Build a kNN spatial graph and return ``(distances, indices)``.

    Parameters
    ----------
    coords : ndarray, shape (n, 2)
        Spatial coordinates.
    k : int
        Number of neighbours (excluding the query point itself when
        *include_self* is ``False``).
    include_self : bool
        If ``False`` (default), the query will use ``k + 1`` neighbours and
        the returned arrays are already clipped (self-edges removed) so that
        each row has exactly *k* entries.  If ``True``, the query uses *k*
        directly.

    Returns
    -------
    distances : ndarray, shape (n, k)
    indices   : ndarray, shape (n, k)
    """
    from sklearn.neighbors import NearestNeighbors

    n = len(coords)
    if include_self:
        k_use = min(k, n)
    else:
        k_use = min(k + 1, n)
    nn = NearestNeighbors(n_neighbors=k_use).fit(coords)
    dists, idx = nn.kneighbors(coords)
    if not include_self and k_use > 1:
        # Drop the first column (self-hit at distance 0)
        dists = dists[:, 1:]
        idx = idx[:, 1:]
    return dists, idx


def score_signature(
    adata: ad.AnnData,
    genes: List[str],
    layer: str = "logcounts",
) -> np.ndarray:
    """Mean expression of available *genes* per observation.

    Handles sparse and dense matrices transparently.
    """
    present = [g for g in genes if g in adata.var_names]
    if not present:
        return np.zeros(adata.n_obs)
    if layer in adata.layers:
        X = adata[:, present].layers[layer]
    else:
        X = adata[:, present].X
    X = to_dense_array(X)
    return X.mean(axis=1)


def normalize_scores(scores: np.ndarray) -> np.ndarray:
    """Min-max normalize *scores* to [0, 1]."""
    s = scores.astype(float)
    smin, smax = s.min(), s.max()
    if smax > smin:
        return (s - smin) / (smax - smin)
    return np.zeros_like(s)


def build_result_adata(
    expression: np.ndarray,
    coords: np.ndarray,
    var_names: "pd.Index | list[str]",  # noqa: F821
    *,
    obs_prefix: str = "cell",
    dtype: type = np.float32,
) -> ad.AnnData:
    """Build an AnnData from reconstructed/baseline expression + spatial coords.

    This pattern appeared verbatim in every baseline method in
    ``mbsi.benchmarks.competitors`` and in the adapter base class.
    """
    import pandas as pd

    result = ad.AnnData(X=np.asarray(expression, dtype=dtype))
    result.var_names = pd.Index(var_names) if not isinstance(var_names, pd.Index) else var_names.copy()
    result.obs_names = pd.Index([f"{obs_prefix}_{i}" for i in range(expression.shape[0])])
    result.obsm["spatial"] = np.asarray(coords)
    return result
