"""Default analysis profile for STOmics Stereo-seq."""

from __future__ import annotations

from typing import Any, Dict, List

STEREO_SEQ_SCALES = ("bin", "cell", "region")

STEREO_SEQ_PROFILE: Dict[str, Any] = {
    "platform": "stereo_seq",
    "display_name": "STOmics Stereo-seq",
    "resolution_class": "ultra_high",
    "default_scale": "bin",
    "selectable_scales": list(STEREO_SEQ_SCALES),
    "pipeline": [
        {"step": "qc", "label": "QC", "required": True},
        {"step": "normalization", "label": "Normalization", "required": True},
        {"step": "bin_selection", "label": "Bin Selection", "required": False, "scale": "bin"},
        {"step": "cell_aggregation", "label": "Cell Aggregation", "required": False, "scale": "cell"},
        {"step": "spatial_clustering", "label": "Spatial Clustering", "required": True},
        {"step": "sv_genes", "label": "Spatially Variable Genes", "required": True},
        {"step": "communication", "label": "Communication", "required": False},
        {"step": "tme", "label": "TME Intelligence", "required": False},
        {"step": "discovery", "label": "Discovery", "required": True},
    ],
    "ui_hints": {
        "bin": "Ultra-high-resolution bin-level analysis (default for Stereo-seq)",
        "cell": "Cell-aggregated expression from CGEF / segmentation",
        "region": "Region-aware clustering and niche detection",
        "recommended_min_bins": 500,
        "supports_multi_scale_zoom": True,
        "overlay_layers": ["bins", "cells", "regions", "histology", "markers", "communication", "niches"],
    },
    "module_mapping": {
        "qc": "preprocess",
        "normalization": "preprocess",
        "bin_selection": "spatial_analysis",
        "cell_aggregation": "spatial_analysis",
        "spatial_clustering": "spatial_analysis",
        "sv_genes": "spatial_analysis",
        "communication": "communication",
        "tme": "tme",
        "discovery": "discovery",
    },
}


def get_stereo_seq_profile(scale: str = "bin") -> Dict[str, Any]:
    """Return profile dict with active scale for workflows and UI."""
    if scale not in STEREO_SEQ_SCALES:
        scale = "bin"
    profile = dict(STEREO_SEQ_PROFILE)
    profile["active_scale"] = scale
    profile["active_pipeline"] = [
        step for step in STEREO_SEQ_PROFILE["pipeline"]
        if step.get("scale") is None or step.get("scale") == scale
    ]
    return profile


def pipeline_steps_for_scale(scale: str) -> List[str]:
    """Ordered step keys for the given analysis scale."""
    return [s["step"] for s in get_stereo_seq_profile(scale)["active_pipeline"]]
