"""
Internal data contract converters.

All loaders must produce an AnnData that satisfies the MBSI minimum contract:

    adata.X                         float32 CSR, spots/cells × genes
    adata.obsm['spatial']           float64 (n, 2) in µm when known
    adata.obs                       at least obs_names set
    adata.var_names                 gene symbols
    adata.uns['mbsi_platform']      dict — platform metadata
    adata.uns['mbsi_readiness']     dict — readiness score + capabilities
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import anndata as ad
import numpy as np
import scipy.sparse as sp


# ---------------------------------------------------------------------------
# Platform metadata stamp
# ---------------------------------------------------------------------------

def stamp_platform_metadata(
    adata: ad.AnnData,
    platform: str,
    display_name: str,
    coordinate_type: str = "unknown",
    resolution: str = "unknown",
    source_files: Optional[list] = None,
    extra: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> ad.AnnData:
    """Write mbsi_platform metadata block into adata.uns."""
    adata.uns["mbsi_platform"] = {
        "platform": platform,
        "display_name": display_name,
        "coordinate_type": coordinate_type,
        "resolution": resolution,
        "source_files": source_files or [],
        **(extra or {}),
    }
    return adata


# ---------------------------------------------------------------------------
# Readiness scoring
# ---------------------------------------------------------------------------

def compute_readiness(adata: ad.AnnData) -> Dict[str, Any]:
    """
    Compute a readiness score (0–100) and capability flags.

    Returns a dict stored in adata.uns['mbsi_readiness'].
    """
    score = 0
    capabilities: Dict[str, bool] = {}
    issues = []
    warnings = []

    # Expression matrix (30 pts)
    if adata.X is not None:
        X = adata.X
        if sp.issparse(X):
            nnz = X.nnz
            total = X.shape[0] * X.shape[1]
        else:
            nnz = int(np.count_nonzero(X))
            total = X.size
        if nnz > 0:
            score += 30
            capabilities["expression_matrix"] = True
        else:
            issues.append("Expression matrix is all zeros")
            capabilities["expression_matrix"] = False
    else:
        issues.append("No expression matrix")
        capabilities["expression_matrix"] = False

    # Spatial coordinates (30 pts)
    if "spatial" in adata.obsm:
        coords = adata.obsm["spatial"]
        if coords.shape[1] >= 2 and len(coords) == adata.n_obs:
            finite = np.all(np.isfinite(coords))
            unique = len(np.unique(coords, axis=0)) > 1
            if finite and unique:
                score += 30
                capabilities["spatial_coords"] = True
            else:
                issues.append("Spatial coordinates are degenerate (non-finite or all same)")
                capabilities["spatial_coords"] = False
        else:
            issues.append(f"Spatial coords shape mismatch: {coords.shape} vs {adata.n_obs} obs")
            capabilities["spatial_coords"] = False
    else:
        issues.append("No spatial coordinates (obsm['spatial'] missing)")
        capabilities["spatial_coords"] = False

    # Gene names (15 pts)
    if adata.n_vars >= 10:
        score += 15
        capabilities["gene_names"] = True
    elif adata.n_vars > 0:
        score += 5
        warnings.append(f"Only {adata.n_vars} genes — very low panel")
        capabilities["gene_names"] = True
    else:
        issues.append("No genes")
        capabilities["gene_names"] = False

    # Cell/spot identity (10 pts)
    if adata.n_obs >= 5:
        score += 10
        capabilities["obs_names"] = True
    else:
        warnings.append(f"Only {adata.n_obs} spots/cells")
        capabilities["obs_names"] = False

    # Cell type annotations (bonus, not scored)
    has_cell_type = any(
        k in adata.obs.columns for k in ("cell_type", "celltype", "leiden", "louvain", "cluster")
    )
    capabilities["cell_types"] = has_cell_type

    # NaN/Inf check (5 pts)
    if adata.X is not None:
        X_check = adata.X.data if sp.issparse(adata.X) else adata.X
        if not (np.any(np.isnan(X_check)) or np.any(np.isinf(X_check))):
            score += 5
        else:
            warnings.append("Expression matrix contains NaN or Inf values")

    # Image (5 pts bonus)
    if "spatial" in adata.uns and "images" in adata.uns.get("spatial", {}):
        score += 5
        capabilities["histology_image"] = True
    elif "image" in adata.uns:
        score += 5
        capabilities["histology_image"] = True
    else:
        capabilities["histology_image"] = False

    # Status label
    if score >= 90:
        status = "Ready for full pipeline"
    elif score >= 70:
        status = "Ready for spatial analysis"
    elif score >= 50:
        status = "Partial — missing optional data"
    else:
        status = "Incomplete — missing required data"

    readiness = {
        "score": min(score, 100),
        "status": status,
        "capabilities": capabilities,
        "issues": issues,
        "warnings": warnings,
    }
    adata.uns["mbsi_readiness"] = readiness
    return readiness


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def ensure_sparse_csr(adata: ad.AnnData) -> ad.AnnData:
    """Guarantee adata.X is float32 CSR."""
    if adata.X is None:
        return adata
    if not sp.issparse(adata.X):
        adata.X = sp.csr_matrix(adata.X.astype(np.float32))
    elif not isinstance(adata.X, sp.csr_matrix):
        adata.X = adata.X.tocsr().astype(np.float32)
    else:
        adata.X = adata.X.astype(np.float32)
    return adata


def ensure_spatial_float64(adata: ad.AnnData) -> ad.AnnData:
    """Cast obsm['spatial'] to float64."""
    if "spatial" in adata.obsm:
        adata.obsm["spatial"] = np.array(adata.obsm["spatial"], dtype=np.float64)
    return adata


def normalise_adata(adata: ad.AnnData) -> ad.AnnData:
    """Apply all normalisation steps in order."""
    adata = ensure_sparse_csr(adata)
    adata = ensure_spatial_float64(adata)
    return adata


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def to_mbsi_contract(
    adata: ad.AnnData,
    platform: str = "unknown",
    display_name: str = "Unknown",
    coordinate_type: str = "cell",
    resolution: str = "unknown",
    source_files: Optional[list] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> ad.AnnData:
    """
    Convert any loaded AnnData into the MBSI internal contract.

    Stamps platform metadata, normalises dtypes, and computes readiness.
    Returns the modified AnnData (in-place + returned for convenience).
    """
    adata = normalise_adata(adata)
    adata = stamp_platform_metadata(
        adata,
        platform=platform,
        display_name=display_name,
        coordinate_type=coordinate_type,
        resolution=resolution,
        source_files=source_files,
        extra=extra,
    )
    compute_readiness(adata)
    return adata
