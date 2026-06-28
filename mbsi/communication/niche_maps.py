"""Niche interaction spatial maps."""

from __future__ import annotations

from typing import Dict, Tuple

import anndata as ad
import numpy as np

from mbsi.communication._utils import get_expression, resolve_gene
from mbsi.communication.diffusion_flux import compute_diffusion_flux


def build_niche_interaction_map(
    adata: ad.AnnData,
    pair: Tuple[str, str],
    layer: str = "logcounts",
    k: int = 6,
) -> Dict:
    """Build spatial niche interaction map data for visualization."""
    lig, rec = pair
    coords = adata.obsm["spatial"]
    flux = compute_diffusion_flux(adata, lig, rec, k=k, layer=layer)
    lig_e = get_expression(adata, lig, layer)
    rec_e = get_expression(adata, rec, layer)
    interaction = lig_e * rec_e

    return {
        "x": coords[:, 0].astype(float),
        "y": coords[:, 1].astype(float),
        "flux": flux.astype(float),
        "interaction": interaction.astype(float),
        "ligand": resolve_gene(adata, lig) or lig,
        "receptor": resolve_gene(adata, rec) or rec,
        "pathway": f"{lig}-{rec}",
    }
