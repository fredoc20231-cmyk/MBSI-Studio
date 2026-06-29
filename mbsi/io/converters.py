"""Normalize ingested AnnData to MBSI internal contract."""

from __future__ import annotations

from typing import Any, Dict, Optional

import anndata as ad
import numpy as np

from mbsi.io.validators import compute_readiness, validate_adata_contract


def _ensure_qc_obs(adata: ad.AnnData) -> None:
    if "total_counts" in adata.obs:
        return
    X = adata.X
    if hasattr(X, "toarray"):
        totals = np.asarray(X.sum(axis=1)).flatten()
    else:
        totals = np.asarray(X.sum(axis=1)).flatten()
    adata.obs["total_counts"] = totals


def normalize_to_contract(
    adata: ad.AnnData,
    platform: str,
    detection: Optional[Dict[str, Any]] = None,
) -> ad.AnnData:
    """Apply internal contract: spatial coords, uns metadata, QC obs."""
    adata = adata.copy()
    adata.var_names_make_unique()
    adata.obs_names_make_unique()
    adata.obs_names = adata.obs_names.astype(str)
    adata.var_names = adata.var_names.astype(str)

    if "spatial" not in adata.obsm:
        if "x" in adata.obs.columns and "y" in adata.obs.columns:
            adata.obsm["spatial"] = adata.obs[["x", "y"]].values.astype(np.float32)

    _ensure_qc_obs(adata)
    score, readiness = compute_readiness(adata, detection)
    adata.uns["mbsi_platform"] = platform
    adata.uns["mbsi_readiness"] = readiness
    adata.uns["mbsi_readiness_score"] = score
    if detection:
        adata.uns["mbsi_detection"] = detection

    contract = validate_adata_contract(adata)
    adata.uns["mbsi_contract"] = contract
    return adata
