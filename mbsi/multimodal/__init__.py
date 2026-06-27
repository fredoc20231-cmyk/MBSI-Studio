"""Multimodal fusion engine."""

from mbsi.multimodal.fusion import fuse_rna_image_protein, build_multimodal_embedding
from mbsi.multimodal.atac import add_atac_features
from mbsi.multimodal.protein import add_protein_features
from mbsi.multimodal.mutation import add_mutation_features
from mbsi.multimodal.clinical import add_clinical_features

__all__ = [
    "fuse_rna_image_protein",
    "add_atac_features",
    "add_protein_features",
    "add_mutation_features",
    "add_clinical_features",
    "build_multimodal_embedding",
]
