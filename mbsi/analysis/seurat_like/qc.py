"""QC for Seurat-like workflow — wraps mbsi.analysis.qc."""

from __future__ import annotations

from typing import List, Tuple

import anndata as ad
import pandas as pd

from mbsi.analysis.qc import compute_qc_metrics, filter_in_tissue, flag_low_quality_spots, qc_summary_table


def run_qc(
    adata: ad.AnnData,
    min_counts: float = 500,
    min_genes: float = 200,
    max_mito: float = 25.0,
    filter_tissue: bool = True,
) -> Tuple[ad.AnnData, pd.DataFrame, List[str]]:
    """Compute QC metrics, filter, return (adata, summary, warnings)."""
    warnings: List[str] = []
    adata = adata.copy()
    if filter_tissue:
        n_before = adata.n_obs
        adata = filter_in_tissue(adata)
        if adata.n_obs < n_before:
            warnings.append(f"Filtered {n_before - adata.n_obs} spots outside tissue.")
    adata = compute_qc_metrics(adata)
    adata = flag_low_quality_spots(adata, min_counts=min_counts, min_genes=min_genes, max_mito=max_mito)
    n_fail = int((~adata.obs["qc_pass"]).sum())
    if n_fail:
        warnings.append(f"{n_fail} spots failed QC thresholds.")
    adata = filter_cells_or_spots(adata)
    summary = qc_summary_table(adata)
    return adata, summary, warnings


def filter_cells_or_spots(adata: ad.AnnData, qc_key: str = "qc_pass") -> ad.AnnData:
    """Filter to cells/spots passing QC."""
    adata = adata.copy()
    if qc_key in adata.obs.columns:
        return adata[adata.obs[qc_key].astype(bool)].copy()
    return adata
