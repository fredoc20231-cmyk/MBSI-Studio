"""Foundation-ready tissue embedding module."""

from mbsi.foundation.embeddings import compute_tissue_embedding
from mbsi.foundation.predict import predict_missing_genes, zero_shot_annotate_regions

__all__ = [
    "compute_tissue_embedding",
    "predict_missing_genes",
    "zero_shot_annotate_regions",
]
