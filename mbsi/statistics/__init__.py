"""Statistics package for Seurat-like workflows."""

from mbsi.statistics.differential import run_cluster_de, run_condition_de
from mbsi.statistics.pseudobulk import run_pseudobulk_de
from mbsi.statistics.replicate_aware import run_replicate_aware_tests
from mbsi.statistics.spatial_de import run_spatial_de

__all__ = [
    "run_cluster_de",
    "run_condition_de",
    "run_pseudobulk_de",
    "run_replicate_aware_tests",
    "run_spatial_de",
]
