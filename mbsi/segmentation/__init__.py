"""Segmentation engine for tissue, nuclei, and compartments."""

from mbsi.segmentation.nuclei import segment_nuclei
from mbsi.segmentation.tissue import segment_tissue
from mbsi.segmentation.compartments import assign_spots_to_compartments, infer_compartment_labels
from mbsi.segmentation.masks import infer_cell_boundaries, voronoi_cell_regions

__all__ = [
    "segment_tissue",
    "segment_nuclei",
    "infer_cell_boundaries",
    "assign_spots_to_compartments",
    "infer_compartment_labels",
    "voronoi_cell_regions",
]
