"""Technology catalog — required files, QC hints, compatible analyses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TechnologySpec:
    key: str
    label: str
    required_files: List[str] = field(default_factory=list)
    optional_files: List[str] = field(default_factory=list)
    compatible_analyses: List[str] = field(default_factory=list)
    qc_metrics: List[str] = field(default_factory=list)
    normalization_strategy: str = ""
    clustering_choices: List[str] = field(default_factory=list)
    segmentation_logic: str = ""
    benchmark_eligibility: str = ""
    report_sections: List[str] = field(default_factory=list)
    notes: str = ""
    milestone_status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "required_files": list(self.required_files),
            "optional_files": list(self.optional_files),
            "compatible_analyses": list(self.compatible_analyses),
            "qc_metrics": list(self.qc_metrics),
            "normalization_strategy": self.normalization_strategy,
            "clustering_choices": list(self.clustering_choices),
            "segmentation_logic": self.segmentation_logic,
            "benchmark_eligibility": self.benchmark_eligibility,
            "report_sections": list(self.report_sections),
            "notes": self.notes,
            "milestone_status": self.milestone_status,
        }


_MILESTONE_ANALYSES = [
    "study_data",
    "qc_transformation",
    "visualization",
    "spatial_variable_genes",
    "spatial_domains",
    "phenotyping",
    "report_export",
]

_COMMON_ANALYSES = _MILESTONE_ANALYSES + [
    "spatial_gene_sets",
    "differential_analysis",
    "spatial_gradients",
    "segment_register",
    "reconstruction",
    "discovery",
]

MILESTONE_1_PLATFORMS = ("visium", "xenium", "generic_h5ad")
MILESTONE_TECHNOLOGY_KEYS = MILESTONE_1_PLATFORMS

TECHNOLOGY_CATALOG: Dict[str, TechnologySpec] = {
    "visium": TechnologySpec(
        key="visium",
        label="10x Visium",
        required_files=[
            "filtered_feature_bc_matrix.h5 or matrix.mtx",
            "spatial/tissue_positions_list.csv",
        ],
        optional_files=[
            "spatial/scalefactors_json.json",
            "spatial/tissue_hires_image.png",
            "spatial/tissue_lowres_image.png",
        ],
        compatible_analyses=list(_MILESTONE_ANALYSES),
        qc_metrics=["spots_under_tissue", "total_counts", "n_genes", "mito_pct", "ribo_pct"],
        normalization_strategy="SCTransform or log1p + scale (Scanpy)",
        clustering_choices=["Leiden", "Louvain", "BayesSpace (optional)"],
        segmentation_logic="Spot-level (55 µm); histology-guided refinement optional",
        benchmark_eligibility="Out of Milestone 1 scope",
        report_sections=["QC spatial map", "cluster markers", "Moran's I", "domain summary"],
        notes="Milestone 1: Space Ranger outs (h5/mtx + tissue positions + scalefactors + image)",
    ),
    "visium_hd": TechnologySpec(
        key="visium_hd",
        label="10x Visium HD",
        milestone_status="coming_later",
        required_files=[
            "binned_outputs (e.g. square_008um)",
            "spatial/tissue_positions.parquet or csv",
            "scalefactors_json.json",
            "tissue image (H&E)",
        ],
        compatible_analyses=_COMMON_ANALYSES + ["benchmark"],
        qc_metrics=["bin counts", "umi_per_bin", "mito_pct", "tissue coverage"],
        normalization_strategy="Bin-level normalization; aggregate to cell bins for clustering",
        clustering_choices=["Leiden on 8µm bins", "cell-segmentation assisted clusters"],
        segmentation_logic="8µm bin grid + optional cell segmentation pipeline",
        benchmark_eligibility="Yes with matched-resolution reference",
        report_sections=["bin QC", "segmentation overlay", "HD marker panels"],
    ),
    "xenium": TechnologySpec(
        key="xenium",
        label="10x Xenium",
        required_files=[
            "cell_feature_matrix.h5",
            "cells.csv.gz or cells.parquet",
        ],
        optional_files=[
            "transcripts.parquet",
            "cell_boundaries.parquet",
            "morphology.ome.tif",
        ],
        compatible_analyses=list(_MILESTONE_ANALYSES),
        qc_metrics=["transcripts_per_cell", "negative control probes", "cell area", "segmentation quality"],
        normalization_strategy="Per-cell depth normalization; log1p + scale (Scanpy)",
        clustering_choices=["Leiden", "Louvain"],
        segmentation_logic="Cell segmentation from Xenium pipeline (nucleus + membrane)",
        benchmark_eligibility="Out of Milestone 1 scope",
        report_sections=["cell QC", "spatial cell map", "SVG", "domain summary"],
        notes="Milestone 1: real bundle loader (matrix + cells table + optional artifacts)",
    ),
    "merfish": TechnologySpec(
        key="merfish",
        label="MERFISH / MERSCOPE",
        milestone_status="coming_later",
        required_files=[
            "counts matrix (csv/h5ad)",
            "cell metadata with x/y coordinates",
            "segmentation mask or cell boundaries (optional)",
        ],
        compatible_analyses=_COMMON_ANALYSES,
        qc_metrics=["counts per cell", "blank codeword rate", "cell volume", "FOV registration"],
        normalization_strategy="Size-factor normalization; blank subtraction",
        clustering_choices=["Leiden", "Harmony batch correction across FOVs"],
        segmentation_logic="Vizgen MERSCOPE cell segmentation or custom masks",
        benchmark_eligibility="Limited without matched reference",
        report_sections=["FOV QC", "cell type map", "spatial stats"],
        notes="Loader stub — partial support",
    ),
    "cosmx": TechnologySpec(
        key="cosmx",
        label="NanoString CosMx",
        milestone_status="coming_later",
        required_files=[
            "flatFiles/*_exprMat_file.csv",
            "fov_positions_file.csv",
            "metadata_file.csv",
            "morphology images (optional)",
        ],
        compatible_analyses=_COMMON_ANALYSES,
        qc_metrics=["nCount", "nFeature", "neg probes", "cell area", "FOV quality"],
        normalization_strategy="Q3 normalization or SCTransform on CosMx exports",
        clustering_choices=["Leiden", "Seurat workflow on exported matrices"],
        segmentation_logic="CosMx SMI cell segmentation",
        benchmark_eligibility="Partial with scRNA deconvolution reference",
        report_sections=["FOV overview", "niche analysis", "pathway scores"],
        notes="Loader stub — partial support",
    ),
    "stereo_seq": TechnologySpec(
        key="stereo_seq",
        label="STOmics Stereo-seq",
        milestone_status="coming_later",
        required_files=[
            "GEF or CGEF expression matrix",
            "SAW / StereoMap workflow outputs",
            "registered H&E or mIF images",
            "tissue/cell segmentation masks",
            "clustering outputs (optional)",
            "lasso/region selection exports (optional)",
            "HTML QC report from StereoMap (optional)",
        ],
        compatible_analyses=_COMMON_ANALYSES + ["benchmark"],
        qc_metrics=[
            "gene types detected",
            "MID counts",
            "tissue area covered",
            "segmentation overlap",
            "cluster purity",
            "registration alignment score",
        ],
        normalization_strategy="SAW default normalization; bin/cell aggregation from GEF",
        clustering_choices=["SAW clustering", "Leiden on exported AnnData", "region-aware clustering"],
        segmentation_logic="SAW tissue/cell segmentation; StereoMap lasso regions; H&E/mIF guided",
        benchmark_eligibility="Yes when ground-truth cells exported from SAW",
        report_sections=[
            "StereoMap HTML QC summary",
            "GEF coverage map",
            "segmentation overlay",
            "cluster markers",
            "region lasso comparisons",
        ],
        notes="Supports SAW/StereoMap, GEF/CGEF detection; parse partially stubbed",
    ),
    "codex": TechnologySpec(
        key="codex",
        label="CODEX / multiplex IF",
        milestone_status="coming_later",
        required_files=[
            "cell intensity matrix (csv)",
            "cell coordinates / segmentation",
            "channel marker panel definition",
        ],
        optional_files=["tissue image (tif/ome)", "cell masks (tiff/png)"],
        compatible_analyses=["qc_preprocess", "segment_register", "spatial_analysis", "discovery", "report_export"],
        qc_metrics=["signal-to-noise per channel", "cell segmentation quality", "background staining"],
        normalization_strategy="Arcsinh or percentile normalization per marker",
        clustering_choices=["Phenograph", "Leiden on protein profiles"],
        segmentation_logic="CellProfiler / CODEX Toolkit segmentation",
        benchmark_eligibility="No standard gene-level benchmark",
        report_sections=["marker heatmap", "neighborhood analysis", "immune infiltration"],
        notes="Loader stub — partial support",
    ),
    "spatial_atac": TechnologySpec(
        key="spatial_atac",
        label="Spatial ATAC",
        milestone_status="coming_later",
        required_files=[
            "peak-by-spot matrix (h5ad or mtx)",
            "spatial coordinates",
            "fragment file or BAM (optional)",
            "linked gene activity scores (optional)",
        ],
        compatible_analyses=["qc_preprocess", "segment_register", "spatial_analysis", "discovery", "report_export"],
        qc_metrics=["FRiP", "TSS enrichment", "mitochondrial reads", "duplicate rate"],
        normalization_strategy="TF-IDF or Signac workflow normalization",
        clustering_choices=["LSI + Leiden", "Signac clusters"],
        segmentation_logic="Spot or bin level; linked to histology when available",
        benchmark_eligibility="Limited — requires matched scATAC reference",
        report_sections=["peak accessibility map", "gene activity", "motif enrichment"],
        notes="Loader stub — partial support",
    ),
    "slide_seq": TechnologySpec(
        key="slide_seq",
        label="Slide-seq",
        milestone_status="coming_later",
        required_files=[
            "bead-by-gene matrix (csv/h5ad/mtx)",
            "bead locations (csv with x/y or puck coordinates)",
            "puck layout / array coordinates",
        ],
        optional_files=[
            "H&E histology image",
            "registered histology overlay",
            "barcode-to-location mapping file",
        ],
        compatible_analyses=_COMMON_ANALYSES,
        qc_metrics=["beads_under_tissue", "UMI per bead", "gene diversity", "puck coverage", "saturation"],
        normalization_strategy="SCTransform or log-normalization on bead counts",
        clustering_choices=["Leiden on beads", "Puck-aware spatial clustering"],
        segmentation_logic="Bead-level (10 µm); histology-guided puck registration",
        benchmark_eligibility="Limited — requires matched scRNA reference",
        report_sections=["puck QC map", "bead saturation", "spatial gene expression", "SVG"],
        notes="Slide-seq / Slide-seqV2 puck data; parser partial support",
    ),
    "generic_h5ad": TechnologySpec(
        key="generic_h5ad",
        label="Generic AnnData / CSV",
        required_files=[
            "counts matrix (.h5ad or csv)",
            "spatial coordinates (obsm['spatial'] or coordinates.csv)",
        ],
        compatible_analyses=list(_MILESTONE_ANALYSES),
        qc_metrics=["total_counts", "n_genes", "mito_pct", "spatial density"],
        normalization_strategy="log1p + scale (Scanpy default)",
        clustering_choices=["Leiden", "Louvain"],
        segmentation_logic="Use obs cell_type/cluster if present; else spot/cell-level",
        benchmark_eligibility="Out of Milestone 1 scope",
        report_sections=["generic QC", "spatial map", "marker table"],
        notes="Milestone 1: h5ad or CSV matrix + coordinates.csv fallback",
    ),
    "seqfish": TechnologySpec(
        key="seqfish",
        label="SeqFISH+",
        required_files=[
            "cell x gene counts (.h5ad or csv)",
            "cell centroid coordinates (obsm['spatial'] or coordinates.csv)",
        ],
        optional_files=["field-of-view metadata", "segmentation masks"],
        compatible_analyses=list(_MILESTONE_ANALYSES),
        qc_metrics=["total_counts", "n_genes", "mito_pct", "cell density"],
        normalization_strategy="log1p + scale; volume normalization if segmentation present",
        clustering_choices=["Leiden", "Louvain"],
        segmentation_logic="Imaging-based single-cell segmentation (nucleus/cytoplasm masks)",
        benchmark_eligibility="Yes with matched-resolution reference",
        report_sections=["QC", "spatial map", "marker table", "cell neighborhoods"],
        milestone_status="coming_later",
        notes="SeqFISH+ high-plex imaging; export to h5ad (cells × genes + spatial) for ingestion",
    ),
    "exst": TechnologySpec(
        key="exst",
        label="Expansion Spatial Transcriptomics (ExST)",
        required_files=[
            "cell/spot x gene counts (.h5ad or csv)",
            "expansion-corrected coordinates (obsm['spatial'])",
        ],
        optional_files=["expansion factor metadata", "segmentation masks"],
        compatible_analyses=list(_MILESTONE_ANALYSES),
        qc_metrics=["total_counts", "n_genes", "mito_pct", "cell density"],
        normalization_strategy="log1p + scale (coordinates rescaled by expansion factor)",
        clustering_choices=["Leiden", "Louvain"],
        segmentation_logic="Imaging-based segmentation on expanded tissue; rescale coords by expansion factor",
        benchmark_eligibility="Yes with matched-resolution reference",
        report_sections=["QC", "spatial map", "marker table"],
        milestone_status="coming_later",
        notes="ExST: divide physical coordinates by expansion factor before analysis",
    ),
}

TECHNOLOGY_LABELS: Dict[str, str] = {k: v.label for k, v in TECHNOLOGY_CATALOG.items()}

UI_TECHNOLOGY_OPTIONS = [
    ("10x Visium", "visium"),
    ("10x Xenium", "xenium"),
    ("Generic AnnData / CSV", "generic_h5ad"),
]

COMING_LATER_UI_TECHNOLOGY_OPTIONS = [
    ("10x Visium HD", "visium_hd"),
    ("MERFISH / MERSCOPE", "merfish"),
    ("NanoString CosMx", "cosmx"),
    ("STOmics Stereo-seq", "stereo_seq"),
    ("CODEX / multiplex IF", "codex"),
    ("Slide-seq", "slide_seq"),
    ("Spatial ATAC", "spatial_atac"),
    ("SeqFISH+", "seqfish"),
    ("Expansion Spatial Transcriptomics (ExST)", "exst"),
]

# Full catalog labels (non-milestone platforms remain in TECHNOLOGY_CATALOG for reference)
ALL_UI_TECHNOLOGY_OPTIONS = UI_TECHNOLOGY_OPTIONS + COMING_LATER_UI_TECHNOLOGY_OPTIONS


def is_milestone_platform(key: Optional[str]) -> bool:
    """Return True when *key* is in Milestone 1 functional scope."""
    return bool(key) and key in MILESTONE_1_PLATFORMS


def normalize_technology_hint(hint: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Map API/UI technology hints to Milestone 1 keys; return (key, warning)."""
    if not hint:
        return None, None
    normalized = hint.strip().lower()
    aliases = {"csv_matrix": "generic_h5ad", "h5ad": "generic_h5ad", "generic": "generic_h5ad"}
    normalized = aliases.get(normalized, normalized)
    if is_milestone_platform(normalized):
        return normalized, None
    spec = TECHNOLOGY_CATALOG.get(normalized)
    label = spec.label if spec else normalized
    return None, f"Technology '{label}' is not in Milestone 1 scope — use visium, xenium, or generic_h5ad"


def get_technology(key: str) -> Optional[TechnologySpec]:
    return TECHNOLOGY_CATALOG.get(key)


def technology_from_label(label: str) -> Optional[str]:
    for ui_label, key in ALL_UI_TECHNOLOGY_OPTIONS:
        if ui_label == label or key == label:
            return key if is_milestone_platform(key) else None
    return None


# Capability flags for workflow gating (stereo_seq fully specified; others inferred)
_PLATFORM_CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "visium": {
        "resolution_class": "spot",
        "supports_images": True,
        "supports_segmentation": False,
        "supports_bins": False,
        "supports_cells": False,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": True,
    },
    "visium_hd": {
        "resolution_class": "high",
        "supports_images": True,
        "supports_segmentation": True,
        "supports_bins": True,
        "supports_cells": True,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": True,
    },
    "xenium": {
        "resolution_class": "subcellular",
        "supports_images": True,
        "supports_segmentation": True,
        "supports_bins": False,
        "supports_cells": True,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": True,
    },
    "cosmx": {
        "resolution_class": "single_cell",
        "supports_images": True,
        "supports_segmentation": True,
        "supports_bins": False,
        "supports_cells": True,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": True,
    },
    "merfish": {
        "resolution_class": "single_cell",
        "supports_images": True,
        "supports_segmentation": True,
        "supports_bins": False,
        "supports_cells": True,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": True,
    },
    "codex": {
        "resolution_class": "single_cell",
        "supports_images": True,
        "supports_segmentation": True,
        "supports_bins": False,
        "supports_cells": True,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": True,
    },
    "spatial_atac": {
        "resolution_class": "spot",
        "supports_images": True,
        "supports_segmentation": False,
        "supports_bins": True,
        "supports_cells": False,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": False,
    },
    "stereo_seq": {
        "display_name": "STOmics Stereo-seq",
        "resolution_class": "ultra_high",
        "supports_images": True,
        "supports_segmentation": True,
        "supports_bins": True,
        "supports_cells": True,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": True,
    },
    "slide_seq": {
        "resolution_class": "near_single_cell",
        "supports_images": False,
        "supports_segmentation": False,
        "supports_bins": True,
        "supports_cells": False,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": False,
    },
    "seqfish": {
        "resolution_class": "single_cell",
        "supports_images": True,
        "supports_segmentation": True,
        "supports_bins": False,
        "supports_cells": True,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": True,
    },
    "exst": {
        "resolution_class": "subcellular",
        "supports_images": True,
        "supports_segmentation": True,
        "supports_bins": False,
        "supports_cells": True,
        "supports_regions": True,
        "supports_ground_truth_benchmarking": True,
    },
    "generic_h5ad": {
        "resolution_class": "generic",
        "supports_images": True,
        "supports_segmentation": True,
        "supports_bins": False,
        "supports_cells": False,
        "supports_regions": False,
        "supports_ground_truth_benchmarking": False,
    },
}


# Human-readable presentation fields consumed by the AIStudio React frontend.
# `resolution` and `modality_type` populate StudySetupView's currentTech.resolution
# and currentTech.type — the fields whose absence previously threw a TypeError.
_PLATFORM_PRESENTATION: Dict[str, Dict[str, str]] = {
    "visium": {"resolution": "55 µm spots", "modality_type": "Sequencing-based"},
    "visium_hd": {"resolution": "2–8 µm bins", "modality_type": "Sequencing-based"},
    "xenium": {"resolution": "Subcellular (~0.2 µm)", "modality_type": "Imaging-based"},
    "merfish": {"resolution": "Subcellular", "modality_type": "Imaging-based"},
    "cosmx": {"resolution": "Single-cell / subcellular", "modality_type": "Imaging-based"},
    "stereo_seq": {"resolution": "220–500 nm (DNB)", "modality_type": "Sequencing-based"},
    "codex": {"resolution": "Single-cell (protein)", "modality_type": "Imaging-based"},
    "spatial_atac": {"resolution": "Spot / bin (epigenome)", "modality_type": "Sequencing-based"},
    "slide_seq": {"resolution": "10 µm beads", "modality_type": "Sequencing-based"},
    "seqfish": {"resolution": "Subcellular", "modality_type": "Imaging-based"},
    "exst": {"resolution": "Subcellular (expansion)", "modality_type": "Imaging-based"},
    "generic_h5ad": {"resolution": "Variable", "modality_type": "Generic"},
}


def _technology_entry(key: str, spec: TechnologySpec) -> Dict[str, Any]:
    caps = _PLATFORM_CAPABILITIES.get(key, {})
    pres = _PLATFORM_PRESENTATION.get(key, {})
    return {
        # AIStudio frontend contract fields (id/name/resolution/type) — additive aliases.
        "id": key,
        "name": caps.get("display_name", spec.label),
        "resolution": pres.get("resolution", "Variable"),
        "type": pres.get("modality_type", "Generic"),
        "display_name": caps.get("display_name", spec.label),
        "resolution_class": caps.get("resolution_class", "generic"),
        "supports_images": caps.get("supports_images", True),
        "supports_segmentation": caps.get("supports_segmentation", False),
        "supports_bins": caps.get("supports_bins", False),
        "supports_cells": caps.get("supports_cells", False),
        "supports_regions": caps.get("supports_regions", False),
        "supports_ground_truth_benchmarking": caps.get("supports_ground_truth_benchmarking", False),
        "required_files": list(spec.required_files),
        "optional_files": list(spec.optional_files),
        "compatible_analyses": list(spec.compatible_analyses),
        "qc_metrics": list(spec.qc_metrics),
        "normalization": spec.normalization_strategy,
        "clustering": list(spec.clustering_choices),
        "benchmark_eligibility": spec.benchmark_eligibility,
        "report_sections": list(spec.report_sections),
        "notes": spec.notes,
        "milestone_status": spec.milestone_status,
        "milestone_1_functional": is_milestone_platform(key),
    }


TECHNOLOGIES: Dict[str, Dict[str, Any]] = {
    key: _technology_entry(key, spec) for key, spec in TECHNOLOGY_CATALOG.items()
}


def list_technologies() -> List[str]:
    return list(TECHNOLOGY_CATALOG.keys())


def list_technologies_api() -> List[Dict[str, Any]]:
    """Technology catalog for API responses — milestone scope annotated."""
    out: List[Dict[str, Any]] = []
    for key, spec in TECHNOLOGY_CATALOG.items():
        entry = _technology_entry(key, spec)
        entry["key"] = key
        out.append(entry)
    return out
