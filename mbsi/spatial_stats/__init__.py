"""Spatial statistics — re-exports from mbsi.analysis.spatial_stats and .svg."""

from mbsi.analysis.spatial_stats import (
    build_spatial_weights,
    gearys_c,
    morans_i,
    spatial_autocorrelation_table,
)
from mbsi.analysis.svg import (
    benjamini_hochberg,
    detect_svgs,
    gearys_c_vectorized,
    morans_i_vectorized,
)

__all__ = [
    "build_spatial_weights",
    "gearys_c",
    "morans_i",
    "spatial_autocorrelation_table",
    # Rigorous SVG detection (significance-tested)
    "detect_svgs",
    "morans_i_vectorized",
    "gearys_c_vectorized",
    "benjamini_hochberg",
]
