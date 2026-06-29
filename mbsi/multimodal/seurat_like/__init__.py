"""Multimodal Seurat-like integration."""

from mbsi.multimodal.seurat_like.wnn import run_weighted_nearest_neighbor
from mbsi.multimodal.seurat_like.reference_mapping import run_reference_mapping, map_query_to_reference
from mbsi.multimodal.seurat_like.bridge_integration import run_bridge_integration
from mbsi.multimodal.seurat_like.rna_atac import integrate_rna_atac
from mbsi.multimodal.seurat_like.protein import integrate_rna_protein

__all__ = [
    "run_weighted_nearest_neighbor",
    "run_reference_mapping",
    "map_query_to_reference",
    "run_bridge_integration",
    "integrate_rna_atac",
    "integrate_rna_protein",
]
