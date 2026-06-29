"""Multimodal analysis presets (RNA+ATAC, RNA+protein, RNA+histology, RNA+mutation)."""

from __future__ import annotations

from typing import Any, Dict, List

MULTIMODAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "rna_atac": {
        "label": "RNA + ATAC",
        "modalities": ["rna", "atac"],
        "integration_method": "bridge",
        "reductions": ["pca_rna", "lsi_atac"],
        "clustering": "wnn",
        "fallback": "concat_pca",
    },
    "rna_protein": {
        "label": "RNA + protein",
        "modalities": ["rna", "protein"],
        "integration_method": "wnn",
        "reductions": ["pca_rna", "pca_protein"],
        "clustering": "wnn",
        "fallback": "concat_pca",
    },
    "rna_histology": {
        "label": "RNA + histology",
        "modalities": ["rna", "image"],
        "integration_method": "bridge",
        "reductions": ["pca_rna", "image_features"],
        "clustering": "Leiden",
        "fallback": "rna_only",
    },
    "rna_mutation": {
        "label": "RNA + mutation",
        "modalities": ["rna", "mutation"],
        "integration_method": "metadata_overlay",
        "reductions": ["pca_rna"],
        "clustering": "Leiden",
        "fallback": "rna_only",
    },
}


def list_multimodal_presets() -> List[str]:
    return list(MULTIMODAL_PRESETS.keys())


def get_multimodal_preset(key: str) -> Dict[str, Any]:
    if key not in MULTIMODAL_PRESETS:
        key = "rna_protein"
    preset = dict(MULTIMODAL_PRESETS[key])
    preset["key"] = key
    return preset
