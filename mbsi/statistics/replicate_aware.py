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
    if sample_key not in adata.obs.columns:
        warnings.append(f"Missing {sample_key} — falling back to spot-level condition DE.")
        from mbsi.statistics.differential import run_condition_de

        de = run_condition_de(adata, condition_key=condition_key)
        return {"de_results": de, "method": "spot_level", "warnings": warnings}

    n_reps = adata.obs[replicate_key].nunique() if replicate_key in adata.obs.columns else 0
    if n_reps < 2:
        warnings.append("Fewer than 2 replicates — pseudobulk may be underpowered.")

    de = run_pseudobulk_de(adata, sample_key=sample_key, group_key=condition_key)
    return {
        "de_results": de,
        "method": "pseudobulk",
        "n_replicates": n_reps,
        "warnings": warnings,
    }
