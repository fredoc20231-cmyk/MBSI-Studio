"""Quality control metrics for spatial transcriptomics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import anndata as ad

from mbsi.utils import to_dense_array


def compute_qc_metrics(adata: ad.AnnData, mito_prefixes: tuple = ("MT-", "mt-")) -> ad.AnnData:
    """Add total_counts, n_genes_by_counts, pct_counts_mito, log1p_total_counts to obs."""
    adata = adata.copy()
    X = to_dense_array(adata.X)
    totals = X.sum(axis=1)
    n_genes = (X > 0).sum(axis=1)

    mito_mask = np.zeros(adata.n_vars, dtype=bool)
    for prefix in mito_prefixes:
        mito_mask |= adata.var_names.str.startswith(prefix)

    if mito_mask.any():
        mito = adata[:, mito_mask].X
        mito_sum = np.asarray(mito.sum(axis=1)).flatten() if hasattr(mito, "sum") else mito.sum(axis=1)
        pct_mito = 100.0 * mito_sum / (totals + 1e-12)
    else:
        pct_mito = np.zeros(adata.n_obs)

    adata.obs["total_counts"] = totals
    adata.obs["n_genes_by_counts"] = n_genes
    adata.obs["pct_counts_mito"] = pct_mito
    adata.obs["log1p_total_counts"] = np.log1p(totals)
    return adata


def filter_in_tissue(adata: ad.AnnData) -> ad.AnnData:
    """Return copy where obs['in_tissue'] is True."""
    if "in_tissue" not in adata.obs.columns:
        return adata.copy()
    return adata[adata.obs["in_tissue"].astype(bool)].copy()


def qc_summary_table(adata: ad.AnnData) -> pd.DataFrame:
    """Return dataframe with median/mean/min/max QC values."""
    cols = ["total_counts", "n_genes_by_counts", "pct_counts_mito"]
    rows = []
    for c in cols:
        if c not in adata.obs.columns:
            continue
        s = adata.obs[c]
        rows.append({
            "metric": c,
            "median": float(s.median()),
            "mean": float(s.mean()),
            "min": float(s.min()),
            "max": float(s.max()),
        })
    return pd.DataFrame(rows)


def flag_low_quality_spots(
    adata: ad.AnnData,
    min_counts: float = 500,
    min_genes: float = 200,
    max_mito: float = 25.0,
) -> ad.AnnData:
    """Add obs['qc_pass'] boolean."""
    adata = adata.copy()
    if "total_counts" not in adata.obs.columns:
        adata = compute_qc_metrics(adata)
    adata.obs["qc_pass"] = (
        (adata.obs["total_counts"] >= min_counts)
        & (adata.obs["n_genes_by_counts"] >= min_genes)
        & (adata.obs["pct_counts_mito"] <= max_mito)
    )
    return adata
