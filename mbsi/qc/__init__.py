"""QC summary and filtering — delegates to seurat_like where possible."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.analysis.qc import compute_qc_metrics, filter_in_tissue, flag_low_quality_spots, qc_summary_table
from mbsi.analysis.seurat_like.qc import filter_cells_or_spots


def compute_original_summary(adata: ad.AnnData) -> pd.DataFrame:
    """Min/mean/max counts, genes, mito %, in-tissue %, sample totals."""
    adata = adata.copy()
    if "total_counts" not in adata.obs.columns:
        adata = compute_qc_metrics(adata)
    obs = adata.obs
    rows: List[Dict[str, Any]] = []
    group_keys = ["sample_id"] if "sample_id" in obs.columns else [None]
    for gk in group_keys:
        if gk:
            for sid, sub in obs.groupby(gk):
                rows.append(_summary_row(sub, str(sid)))
        else:
            rows.append(_summary_row(obs, "all"))
    return pd.DataFrame(rows)


def _summary_row(obs: pd.DataFrame, label: str) -> Dict[str, Any]:
    tc = obs.get("total_counts", pd.Series(dtype=float))
    ng = obs.get("n_genes_by_counts", obs.get("n_genes", pd.Series(dtype=float)))
    mito = obs.get("pct_counts_mt", obs.get("mito_pct", pd.Series(dtype=float)))
    in_tissue = obs.get("in_tissue", pd.Series(dtype=float))
    return {
        "sample": label,
        "n_spots": len(obs),
        "counts_min": float(tc.min()) if len(tc) else 0,
        "counts_mean": float(tc.mean()) if len(tc) else 0,
        "counts_max": float(tc.max()) if len(tc) else 0,
        "genes_min": float(ng.min()) if len(ng) else 0,
        "genes_mean": float(ng.mean()) if len(ng) else 0,
        "genes_max": float(ng.max()) if len(ng) else 0,
        "mito_pct_mean": float(mito.mean()) if len(mito) else 0,
        "in_tissue_pct": float(in_tissue.mean() * 100) if len(in_tissue) else 100.0,
    }


def filter_data(
    adata: ad.AnnData,
    *,
    sample_ids: Optional[List[str]] = None,
    gene_name_pattern: str = "",
    min_counts: float = 0,
    max_counts: Optional[float] = None,
    min_genes: float = 0,
    max_genes: Optional[float] = None,
    min_cells_expressing: int = 0,
    max_mito_pct: float = 100.0,
    filter_tissue: bool = True,
) -> Tuple[ad.AnnData, pd.DataFrame, List[str]]:
    """Filter in order: samples → genes by name → spots/cells → genes by count."""
    warnings: List[str] = []
    adata = adata.copy()

    if sample_ids and "sample_id" in adata.obs.columns:
        n_before = adata.n_obs
        adata = adata[adata.obs["sample_id"].astype(str).isin(sample_ids)].copy()
        if adata.n_obs < n_before:
            warnings.append(f"Filtered to {len(sample_ids)} sample(s): removed {n_before - adata.n_obs} spots.")

    if gene_name_pattern:
        import re

        pat = re.compile(gene_name_pattern, re.IGNORECASE)
        keep_genes = [g for g in adata.var_names if pat.search(str(g))]
        if keep_genes:
            adata = adata[:, keep_genes].copy()
            warnings.append(f"Gene name filter kept {len(keep_genes)} genes.")
        else:
            warnings.append("Gene name filter matched no genes — skipped.")

    if filter_tissue:
        n_before = adata.n_obs
        adata = filter_in_tissue(adata)
        if adata.n_obs < n_before:
            warnings.append(f"Removed {n_before - adata.n_obs} spots outside tissue.")

    adata = compute_qc_metrics(adata)
    adata = flag_low_quality_spots(
        adata,
        min_counts=min_counts,
        min_genes=min_genes,
        max_mito=max_mito_pct,
    )
    if max_counts is not None and "total_counts" in adata.obs:
        adata.obs["qc_pass"] = adata.obs["qc_pass"] & (adata.obs["total_counts"] <= max_counts)
    if max_genes is not None:
        ng_col = "n_genes_by_counts" if "n_genes_by_counts" in adata.obs else "n_genes"
        if ng_col in adata.obs:
            adata.obs["qc_pass"] = adata.obs["qc_pass"] & (adata.obs[ng_col] <= max_genes)

    n_fail = int((~adata.obs["qc_pass"]).sum()) if "qc_pass" in adata.obs else 0
    if n_fail:
        warnings.append(f"{n_fail} spots failed QC thresholds.")
    adata = filter_cells_or_spots(adata)

    if min_cells_expressing > 0:
        X = adata.X
        if hasattr(X, "toarray"):
            X = X.toarray()
        n_cells = np.asarray((X > 0).sum(axis=0)).flatten()
        keep = n_cells >= min_cells_expressing
        if keep.sum() < adata.n_vars:
            adata = adata[:, keep].copy()
            warnings.append(f"Removed genes expressed in < {min_cells_expressing} cells.")

    summary = qc_summary_table(adata)
    return adata, summary, warnings
