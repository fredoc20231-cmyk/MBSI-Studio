"""Foundation-ready tissue embedding module.

Status: RESEARCH — not wired to Milestone 1 UI/API.
See docs/RESEARCH_MODULES.md.
"""

from mbsi.foundation.embeddings import compute_tissue_embedding
from mbsi.foundation.predict import predict_missing_genes, zero_shot_annotate_regions

__all__ = [
    "compute_tissue_embedding",
    "predict_missing_genes",
    "zero_shot_annotate_regions",
]
