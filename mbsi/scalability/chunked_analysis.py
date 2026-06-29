"""Chunked operations for large matrices."""

from __future__ import annotations

from typing import Callable, Iterator

import anndata as ad
import numpy as np


def chunked_apply(
    adata: ad.AnnData,
    fn: Callable[[np.ndarray], np.ndarray],
    chunk_size: int = 5000,
    axis: int = 0,
) -> np.ndarray:
    """Apply function to matrix in chunks along axis 0 (obs)."""
    n = adata.n_obs if axis == 0 else adata.n_vars
    results = []
    X = adata.X
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        chunk = X[start:end] if axis == 0 else X[:, start:end]
        if hasattr(chunk, "toarray"):
            chunk = chunk.toarray()
        results.append(fn(np.asarray(chunk)))
    return np.vstack(results) if axis == 0 else np.hstack(results)


def iter_obs_chunks(adata: ad.AnnData, chunk_size: int = 5000) -> Iterator[ad.AnnData]:
    """Yield AnnData slices by obs chunks."""
    for start in range(0, adata.n_obs, chunk_size):
        end = min(start + chunk_size, adata.n_obs)
        yield adata[start:end].copy()
