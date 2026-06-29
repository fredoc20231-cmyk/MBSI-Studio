"""Transport plan compression for memory-efficient storage."""

from __future__ import annotations

from typing import Any, Dict, Union

import numpy as np
import scipy.sparse


def compress_transport_plan(
    transport_plan: np.ndarray,
    top_k: int = 50,
) -> Dict[str, Any]:
    """
    Store only top-k edges per spot instead of dense (n_spots × n_cells) matrix.

    Dense plan for 5k spots × 25k cells ≈ 1 GB (float64).
    Top-k=50 edges ≈ 250k edges ≈ 3 MB — ~300× savings at scale.

    Parameters
    ----------
    transport_plan : ndarray
        Dense OT plan (n_spots × n_cells)
    top_k : int
        Maximum edges retained per source spot

    Returns
    -------
    sparse_plan : dict
        Edge list plus CSR matrix and memory accounting
    """
    plan = np.asarray(transport_plan, dtype=np.float64)
    n_spots, n_cells = plan.shape
    k = min(top_k, n_cells)

    source_idx: list[int] = []
    target_idx: list[int] = []
    weight: list[float] = []

    for i in range(n_spots):
        row = plan[i]
        if k >= n_cells:
            cols = np.arange(n_cells)
            vals = row
        else:
            cols = np.argpartition(row, -k)[-k:]
            vals = row[cols]
        mask = vals > 1e-12
        source_idx.extend([i] * int(mask.sum()))
        target_idx.extend(cols[mask].tolist())
        weight.extend(vals[mask].tolist())

    src = np.array(source_idx, dtype=np.int32)
    tgt = np.array(target_idx, dtype=np.int32)
    w = np.array(weight, dtype=np.float32)
    csr = scipy.sparse.coo_matrix((w, (src, tgt)), shape=(n_spots, n_cells)).tocsr()

    dense_bytes = n_spots * n_cells * 8
    sparse_bytes = int(w.nbytes + src.nbytes + tgt.nbytes)

    return {
        "format": "top_k_edges",
        "top_k": k,
        "n_spots": n_spots,
        "n_cells": n_cells,
        "source_idx": src,
        "target_idx": tgt,
        "weight": w,
        "csr": csr,
        "memory_dense_bytes": dense_bytes,
        "memory_sparse_bytes": sparse_bytes,
        "memory_savings_ratio": round(dense_bytes / max(sparse_bytes, 1), 1),
    }


def apply_transport_to_expression(
    spot_expression: np.ndarray,
    transport: Union[np.ndarray, Dict[str, Any], scipy.sparse.spmatrix],
) -> np.ndarray:
    """
    Reconstruct cell expression: X_cells = T^T @ X_spots.

    Accepts dense plan, sparse dict from compress_transport_plan, or CSR matrix.
    """
    if hasattr(spot_expression, "toarray"):
        spot_expression = spot_expression.toarray()
    spot_expression = np.asarray(spot_expression, dtype=np.float64)

    if isinstance(transport, dict):
        if "csr" in transport and transport["csr"] is not None:
            return transport["csr"].T @ spot_expression
        n_cells = transport["n_cells"]
        recon = np.zeros((n_cells, spot_expression.shape[1]), dtype=np.float64)
        src = transport["source_idx"]
        tgt = transport["target_idx"]
        w = transport["weight"]
        for edge, (i, j, wt) in enumerate(zip(src, tgt, w)):
            recon[j] += wt * spot_expression[i]
        return recon

    if scipy.sparse.issparse(transport):
        return transport.T @ spot_expression

    return np.asarray(transport).T @ spot_expression
