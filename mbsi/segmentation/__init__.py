"""Segmentation engine for tissue, nuclei, cells, and compartments."""

from mbsi.segmentation.boundaries import (
    compute_boundary_confidence,
    compute_invasion_front_score,
    compute_tumor_stroma_boundary,
    detect_boundaries,
    extract_region_boundaries,
)
from mbsi.segmentation.baseline_unet import (
    UNTRAINED_MESSAGE,
    baseline_unet_weights_available,
    resolve_baseline_unet_weights_path,
    run_baseline_unet_segmentation,
)
from mbsi.segmentation.cellpose_pipeline import run_cellpose_segmentation
from mbsi.segmentation.cells import generate_voronoi_cells, segment_cells, voronoi_label_mask_from_coords
from mbsi.segmentation.compartments import (
    assign_spots_to_compartments,
    infer_compartment_labels,
    segment_compartments,
)
from mbsi.segmentation.export import (
    attach_segmentation_to_adata,
    export_boundaries,
    export_label_mask,
    export_segmentation_masks,
    import_cell_boundaries,
    import_segmentation_mask,
)
from mbsi.segmentation.importers import (
    load_boundary_csv,
    load_boundary_geojson,
    load_segmentation_mask,
    load_xenium_boundaries,
    rasterize_boundaries,
)
from mbsi.segmentation.masks import infer_cell_boundaries, voronoi_cell_regions
from mbsi.segmentation.nuclei import segment_nuclei
from mbsi.segmentation.qc import compute_label_mask_qc, compute_segmentation_qc
from mbsi.segmentation.registration import (
    apply_transform_to_coords,
    estimate_affine_transform,
    register_spatial_to_image,
    validate_registration,
)
from mbsi.segmentation.deepcell_mesmer_pipeline import mesmer_available, run_mesmer_segmentation
from mbsi.segmentation.stardist_pipeline import expand_nuclei_to_cells, run_stardist_nuclei_segmentation
from mbsi.segmentation.tissue import segment_tissue
from mbsi.segmentation.transcript_mapping import build_cell_by_gene_anndata, map_transcripts_to_labels

__all__ = [
    "segment_tissue",
    "segment_nuclei",
    "segment_cells",
    "segment_compartments",
    "detect_boundaries",
    "generate_voronoi_cells",
    "voronoi_label_mask_from_coords",
    "run_stardist_nuclei_segmentation",
    "expand_nuclei_to_cells",
    "run_cellpose_segmentation",
    "run_mesmer_segmentation",
    "mesmer_available",
    "run_baseline_unet_segmentation",
    "baseline_unet_weights_available",
    "resolve_baseline_unet_weights_path",
    "UNTRAINED_MESSAGE",
    "load_xenium_boundaries",
    "load_segmentation_mask",
    "load_boundary_csv",
    "load_boundary_geojson",
    "rasterize_boundaries",
    "map_transcripts_to_labels",
    "build_cell_by_gene_anndata",
    "import_segmentation_mask",
    "import_cell_boundaries",
    "infer_cell_boundaries",
    "assign_spots_to_compartments",
    "infer_compartment_labels",
    "voronoi_cell_regions",
    "attach_segmentation_to_adata",
    "export_segmentation_masks",
    "export_label_mask",
    "export_boundaries",
    "compute_segmentation_qc",
    "compute_label_mask_qc",
    "register_spatial_to_image",
    "estimate_affine_transform",
    "apply_transform_to_coords",
    "validate_registration",
    "extract_region_boundaries",
    "compute_tumor_stroma_boundary",
    "compute_invasion_front_score",
    "compute_boundary_confidence",
]
