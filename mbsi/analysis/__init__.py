"""Core spatial transcriptomics analysis (Visium / Space Ranger workflow)."""

from mbsi.analysis.pipeline import run_standard_spatial_analysis, export_analysis_results, ANALYSIS_GUARDRAIL
from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.analysis.visium import (
    read_visium_spaceranger,
    load_spatial_image,
    load_scalefactors,
    load_tissue_positions,
)
from mbsi.analysis.svg import (
    detect_svgs,
    morans_i_vectorized,
    gearys_c_vectorized,
    benjamini_hochberg,
)

__all__ = [
    "run_standard_spatial_analysis",
    "export_analysis_results",
    "ANALYSIS_GUARDRAIL",
    "make_synthetic_visium_adata",
    "read_visium_spaceranger",
    "load_spatial_image",
    "load_scalefactors",
    "load_tissue_positions",
    "detect_svgs",
    "morans_i_vectorized",
    "gearys_c_vectorized",
    "benjamini_hochberg",
]
