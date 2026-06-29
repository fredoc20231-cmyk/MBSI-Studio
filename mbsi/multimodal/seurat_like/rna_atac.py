"""RNA + ATAC integration."""

from __future__ import annotations

from typing import Tuple

import anndata as ad

from mbsi.multimodal.seurat_like.bridge_integration import run_bridge_integration
from mbsi.multimodal.seurat_like.wnn import run_weighted_nearest_neighbor


def integrate_rna_atac(
    adata: ad.AnnData,
    use_wnn: bool = True,
) -> Tuple[ad.AnnData, str]:
    """Integrate RNA and ATAC modalities."""
    adata = adata.copy()
    if use_wnn:
        return run_weighted_nearest_neighbor(adata, modalities=["rna", "atac"])
    return run_bridge_integration(adata)
