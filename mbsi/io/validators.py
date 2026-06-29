"""Validators and readiness scoring for MBSI data contract."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import anndata as ad
import numpy as np

from mbsi.io.detect import PlatformDetection


def validate_spatial_coords(adata: ad.AnnData) -> Dict[str, Any]:
    """Validate obsm['spatial'] presence and shape."""
    out = {"valid": True, "errors": [], "warnings": []}
    if "spatial" not in adata.obsm:
        out["valid"] = False
        out["errors"].append("Missing obsm['spatial']")
        return out
    coords = adata.obsm["spatial"]
    if coords.shape[0] != adata.n_obs:
        out["valid"] = False
        out["errors"].append(f"Spatial rows {coords.shape[0]} != n_obs {adata.n_obs}")
    if coords.shape[1] != 2:
        out["valid"] = False
        out["errors"].append(f"Spatial must be Nx2, got {coords.shape}")
    if np.isnan(coords).any():
        out["warnings"].append("Spatial coordinates contain NaN")
    return out


def validate_adata_contract(adata: ad.AnnData) -> Dict[str, Any]:
    """Enforce internal MBSI AnnData contract."""
    errors: list[str] = []
    warnings: list[str] = []

    if adata.X is None:
        errors.append("Missing adata.X expression matrix")
    if len(adata.var_names) == 0:
        errors.append("Missing adata.var_names")
    if adata.n_obs == 0:
        errors.append("Zero observations")

    spatial = validate_spatial_coords(adata)
    errors.extend(spatial["errors"])
    warnings.extend(spatial["warnings"])

    if adata.n_obs < 10:
        warnings.append("Very few spots/cells (<10)")
    if adata.n_vars < 50:
        warnings.append("Very few genes (<50)")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "n_spots": adata.n_obs,
        "n_genes": adata.n_vars,
        "has_spatial": "spatial" in adata.obsm,
        "platform": adata.uns.get("mbsi_platform"),
        "readiness": adata.uns.get("mbsi_readiness"),
    }


def compute_readiness(
    adata: ad.AnnData,
    detection: Optional[PlatformDetection] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Compute readiness score 0-100 and detail dict."""
    contract = validate_adata_contract(adata)
    score = 0
    details: Dict[str, Any] = {"checks": {}, "status": "incomplete"}

    if contract["has_spatial"]:
        score += 35
        details["checks"]["spatial"] = True
    if adata.X is not None and adata.n_vars > 0:
        score += 25
        details["checks"]["expression"] = True
    if len(adata.var_names) > 0:
        score += 10
        details["checks"]["genes"] = True

    if "in_tissue" in adata.obs:
        score += 10
        details["checks"]["in_tissue"] = True
    if "total_counts" in adata.obs or "n_genes_by_counts" in adata.obs:
        score += 10
        details["checks"]["qc_obs"] = True
    if adata.uns.get("spatial"):
        score += 10
        details["checks"]["histology_metadata"] = True

    if detection and detection.get("confidence", 0) >= 0.8:
        score = min(100, score + 5)

    if score >= 90:
        details["status"] = "Ready for reconstruction"
    elif score >= 70:
        details["status"] = "Ready for spatial analysis"
    elif score >= 50:
        details["status"] = "Missing optional fields"
    else:
        details["status"] = "Missing required spatial fields"

    details["score"] = score
    details["errors"] = contract["errors"]
    details["warnings"] = contract["warnings"]
    return score, details


def validate_spatial_adata(adata: ad.AnnData) -> Dict[str, Any]:
    """Backward-compatible validator wrapper."""
    return validate_adata_contract(adata)
