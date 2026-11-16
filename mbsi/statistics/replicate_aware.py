"""Replicate-aware statistical tests using sample metadata."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import anndata as ad
import pandas as pd

from mbsi.statistics.pseudobulk import run_pseudobulk_de


def _metadata_from_session(sample_metadata: Any) -> pd.DataFrame:
    if sample_metadata is None:
        return pd.DataFrame()
    if isinstance(sample_metadata, pd.DataFrame):
        return sample_metadata
    if isinstance(sample_metadata, list):
        return pd.DataFrame(sample_metadata)
    return pd.DataFrame()


def run_replicate_aware_tests(
    adata: ad.AnnData,
    sample_metadata: Optional[Any] = None,
    condition_key: str = "condition",
    replicate_key: str = "replicate_id",
    patient_key: str = "patient_id",
) -> Dict[str, Any]:
    """Run replicate-aware DE using sample table metadata."""
    meta = _metadata_from_session(sample_metadata)
    warnings: List[str] = []

    if not meta.empty and "sample_id" in meta.columns:
        if "sample_id" not in adata.obs.columns:
            if adata.n_obs == 1:
                warnings.append("Single observation — cannot map sample metadata.")
            else:
                warnings.append("sample_id not in adata.obs — using obs columns if present.")
        for col in (condition_key, replicate_key, patient_key, "technology", "timepoint"):
            if col in meta.columns and col not in adata.obs.columns and meta.shape[0] == adata.n_obs:
                adata.obs[col] = meta[col].values

    sample_key = "sample_id" if "sample_id" in adata.obs.columns else replicate_key
    if sample_key not in adata.obs.columns or condition_key not in adata.obs.columns:
        warnings.append("BLOCKED: biological sample identifiers and condition labels are required; spots are not replicates.")
        return {"de_results": pd.DataFrame(), "de_table": pd.DataFrame(),
                "method": "blocked", "status": "blocked",
                "reason": "missing_biological_design", "warnings": warnings}

    design = adata.obs[[sample_key, condition_key]].drop_duplicates()
    if design.groupby(sample_key)[condition_key].nunique().gt(1).any():
        warnings.append("BLOCKED: a biological sample is assigned to multiple conditions.")
        return {"de_results": pd.DataFrame(), "de_table": pd.DataFrame(),
                "method": "blocked", "status": "blocked",
                "reason": "ambiguous_sample_condition", "warnings": warnings}

    counts = design.groupby(condition_key)[sample_key].nunique()
    if len(counts) != 2 or (counts < 2).any():
        warnings.append("BLOCKED: at least two independent biological samples per condition are required.")
        return {"de_results": pd.DataFrame(), "de_table": pd.DataFrame(),
                "method": "blocked", "status": "blocked",
                "reason": "insufficient_biological_replicates",
                "n_samples_per_condition": counts.to_dict(), "warnings": warnings}

    # The legacy MWU-on-summed-counts implementation is not a validated
    # negative-binomial differential-expression model. Do not publish its
    # p-values as condition-level evidence until PyDESeq2/edgeR is integrated.
    warnings.append("BLOCKED: validated negative-binomial pseudobulk backend is not configured.")
    return {"de_results": pd.DataFrame(), "de_table": pd.DataFrame(),
            "method": "blocked", "status": "blocked",
            "reason": "validated_de_backend_unavailable",
            "n_samples_per_condition": counts.to_dict(), "warnings": warnings}
