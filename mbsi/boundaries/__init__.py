"""Boundary intelligence engine."""

from mbsi.boundaries.detect import detect_tissue_boundaries
from mbsi.boundaries.leakage import compute_boundary_leakage
from mbsi.boundaries.invasion import detect_invasion_corridors, detect_immune_exclusion_zones

__all__ = [
    "detect_tissue_boundaries",
    "compute_boundary_leakage",
    "detect_invasion_corridors",
    "detect_immune_exclusion_zones",
]
