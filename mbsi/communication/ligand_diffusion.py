"""Diffusion-weighted ligand fields."""

from typing import List, Optional

import anndata as ad
import numpy as np

from mbsi.subcellular.membrane_model import estimate_secreted_ligand_fields


def compute_ligand_diffusion_field(
    adata: ad.AnnData,
    ligand_genes: List[str],
    diffusion_tensor: Optional[np.ndarray] = None,
    sigma: float = 50.0,
) -> np.ndarray:
    """
    Compute ligand diffusion field using spatial Gaussian smoothing.

    If diffusion_tensor provided, scales sigma locally (simplified anisotropy).
    """
    fields = estimate_secreted_ligand_fields(adata, ligand_genes, sigma=sigma)
    if diffusion_tensor is not None and diffusion_tensor.ndim >= 2:
        # Scale by mean tensor trace as proxy for anisotropic diffusion
        scale = np.trace(diffusion_tensor, axis1=-2, axis2=-1).mean() if diffusion_tensor.ndim == 3 else 1.0
        fields = fields * float(scale)
    return fields
