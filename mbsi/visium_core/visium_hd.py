"""Phase 7 — Visium HD: 2/8/16 µm binning, bin-to-cell aggregation and HD-aware QC."""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from .provenance import BlockedAnalysis

VALID_BINS = (2, 8, 16)


def rebin_coordinates(coords_um: np.ndarray, bin_um: int) -> np.ndarray:
    """Map 2 µm barcode coordinates (in microns) to integer bin keys at the target size."""
    if bin_um not in VALID_BINS:
        raise BlockedAnalysis(f"Bin size {bin_um} µm is not supported.", "Use 2, 8 or 16 µm.")
    return np.floor(np.asarray(coords_um, dtype=float) / bin_um).astype(np.int64)


def aggregate(X, keys: np.ndarray):
    from scipy import sparse

    codes, uniq = pd.factorize(pd.Series([f"{a}_{b}" for a, b in keys]))
    n = len(uniq)
    M = sparse.csr_matrix((np.ones(len(codes)), (codes, np.arange(len(codes)))), shape=(n, len(codes)))
    return M @ X, list(uniq)


def visium_hd_bin(adata, params: Dict[str, Any]) -> Dict[str, Any]:
    if "spatial" not in adata.obsm:
        raise BlockedAnalysis("Visium HD data needs barcode coordinates.", "Upload the Space Ranger HD binned_outputs/square_002um folder.")
    bin_um = int(params.get("bin_um", 8))
    microns_per_px = float(params.get("microns_per_pixel", adata.uns.get("microns_per_pixel", 1.0)))
    coords = np.asarray(adata.obsm["spatial"]) * microns_per_px
    keys = rebin_coordinates(coords, bin_um)
    chunk = int(params.get("chunk_size", 500_000))
    if adata.n_obs > chunk:
        # chunked aggregation keeps memory bounded at HD scale
        parts = []
        for s in range(0, adata.n_obs, chunk):
            parts.append(pd.Series(np.asarray(adata.X[s:s + chunk].sum(axis=1)).ravel()).groupby([f"{a}_{b}" for a, b in keys[s:s + chunk]]).sum())
        totals = pd.concat(parts).groupby(level=0).sum()
    else:
        Xb, names = aggregate(adata.X, keys)
        totals = pd.Series(np.asarray(Xb.sum(axis=1)).ravel(), index=names)
    q = totals.quantile([0.05, 0.5, 0.95]).to_dict()
    min_counts = int(params.get("min_counts_per_bin", 10 if bin_um >= 8 else 1))
    return {
        "bin_um": bin_um,
        "n_input_barcodes": int(adata.n_obs),
        "n_bins": int(totals.size),
        "counts_per_bin_quantiles": {str(k): float(v) for k, v in q.items()},
        "bins_passing_qc": int((totals >= min_counts).sum()),
        "min_counts_per_bin": min_counts,
        "segmentation": "bin-to-cell segmentation requires a nucleus mask (params.nucleus_mask); not applied" if not params.get("nucleus_mask") else "mask supplied",
    }
