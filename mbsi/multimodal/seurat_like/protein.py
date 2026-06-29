"""RNA + protein integration."""

from __future__ import annotations

from typing import Tuple

import anndata as ad

from mbsi.multimodal.seurat_like.wnn import run_weighted_nearest_neighbor


def integrate_rna_protein(adata: ad.AnnData) -> Tuple[ad.AnnData, str]:
    """Integrate RNA and protein via WNN or fallback."""
    return run_weighted_nearest_neighbor(adata, modalities=["rna", "protein"])
