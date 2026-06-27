"""
Validators for spatial transcriptomics data.
"""

from typing import Dict, Any

import anndata as ad
import numpy as np


def validate_spatial_adata(adata: ad.AnnData) -> Dict[str, Any]:
    """
    Validate that AnnData has required spatial transcriptomics structure.
    
    Parameters
    ----------
    adata : AnnData
        AnnData object to validate
        
    Returns
    -------
    validation : dict
        Dictionary with validation results:
        - valid: bool
        - errors: list of error messages
        - warnings: list of warning messages
        - n_spots: int
        - n_genes: int
        - has_spatial: bool
    """
    validation = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "n_spots": adata.n_obs,
        "n_genes": adata.n_vars,
        "has_spatial": False,
    }
    
    # Check for spatial coordinates
    if "spatial" in adata.obsm:
        validation["has_spatial"] = True
        coords = adata.obsm["spatial"]
        
        if coords.shape[1] != 2:
            validation["errors"].append(
                f"Spatial coordinates must be 2D, got shape {coords.shape}"
            )
            validation["valid"] = False
        
        if len(coords) != adata.n_obs:
            validation["errors"].append(
                f"Spatial coordinates count ({len(coords)}) doesn't match "
                f"number of spots ({adata.n_obs})"
            )
            validation["valid"] = False
    else:
        validation["errors"].append("No spatial coordinates found in obsm['spatial']")
        validation["valid"] = False
    
    # Check for expression matrix
    if adata.X is None:
        validation["errors"].append("No expression matrix found")
        validation["valid"] = False
    else:
        if adata.X.shape != (adata.n_obs, adata.n_vars):
            validation["errors"].append(
                f"Expression matrix shape {adata.X.shape} doesn't match "
                f"expected ({adata.n_obs}, {adata.n_vars})"
            )
            validation["valid"] = False
    
    # Check for gene names
    if len(adata.var_names) == 0:
        validation["errors"].append("No gene names found")
        validation["valid"] = False
    
    # Check for spot names
    if len(adata.obs_names) == 0:
        validation["errors"].append("No spot names found")
        validation["valid"] = False
    
    # Warnings
    if adata.n_obs < 10:
        validation["warnings"].append(
            f"Very few spots ({adata.n_obs}), results may be unreliable"
        )
    
    if adata.n_vars < 10:
        validation["warnings"].append(
            f"Very few genes ({adata.n_vars}), results may be unreliable"
        )
    
    # Check for NaN values
    if hasattr(adata.X, 'toarray'):
        X_dense = adata.X.toarray()
    else:
        X_dense = adata.X
    
    if np.isnan(X_dense).any():
        validation["warnings"].append("Expression matrix contains NaN values")
    
    if np.isinf(X_dense).any():
        validation["warnings"].append("Expression matrix contains Inf values")
    
    return validation
