"""Segmentation engine for tissue, nuclei, cells, and compartments."""

from mbsi.segmentation.boundaries import (
    compute_boundary_confidence,
    compute_invasion_front_score,
    compute_tumor_stroma_boundary,
    detect_boundaries,
    extract_region_boundaries,
)
from mbsi.segmentation.cells import generate_voronoi_cells, segment_cells
from mbsi.segmentation.compartments import (
    assign_spots_to_compartments,
    infer_compartment_labels,
    segment_compartments,
)
from mbsi.segmentation.export import (
    attach_segmentation_to_adata,
    export_segmentation_masks,
    import_cell_boundaries,
    import_segmentation_mask,
)
from mbsi.segmentation.masks import infer_cell_boundaries, voronoi_cell_regions
from mbsi.segmentation.nuclei import segment_nuclei
from mbsi.segmentation.qc import compute_segmentation_qc
from mbsi.segmentation.registration import (
    apply_transform_to_coords,
    estimate_affine_transform,
    register_spatial_to_image,
    validate_registration,
)
from mbsi.segmentation.tissue import segment_tissue

__all__ = [
    "segment_tissue",
    "segment_nuclei",
    "segment_cells",
    "segment_compartments",
    "detect_boundaries",
    "generate_voronoi_cells",
    "import_segmentation_mask",
    "import_cell_boundaries",
    "infer_cell_boundaries",
    "assign_spots_to_compartments",
    "infer_compartment_labels",
    "voronoi_cell_regions",
    "attach_segmentation_to_adata",
    "export_segmentation_masks",
    "compute_segmentation_qc",
    "register_spatial_to_image",
    "estimate_affine_transform",
    "apply_transform_to_coords",
    "validate_registration",
    "extract_region_boundaries",
    "compute_tumor_stroma_boundary",
    "compute_invasion_front_score",
    "compute_boundary_confidence",
]
