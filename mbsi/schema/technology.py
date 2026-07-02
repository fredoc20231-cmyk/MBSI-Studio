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

MILESTONE_TECHNOLOGY_KEYS = ("visium", "xenium", "generic_h5ad")

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
}

TECHNOLOGY_LABELS: Dict[str, str] = {k: v.label for k, v in TECHNOLOGY_CATALOG.items()}

UI_TECHNOLOGY_OPTIONS = [
    ("10x Visium", "visium"),
    ("10x Xenium", "xenium"),
    ("Generic AnnData / CSV", "generic_h5ad"),
]

# Full catalog labels (non-milestone platforms remain in TECHNOLOGY_CATALOG for reference)
ALL_UI_TECHNOLOGY_OPTIONS = UI_TECHNOLOGY_OPTIONS + [
    ("10x Visium HD", "visium_hd"),
    ("MERFISH / MERSCOPE", "merfish"),
    ("NanoString CosMx", "cosmx"),
    ("STOmics Stereo-seq", "stereo_seq"),
    ("CODEX / multiplex IF", "codex"),
    ("Slide-seq", "slide_seq"),
    ("Spatial ATAC", "spatial_atac"),
]


def get_technology(key: str) -> Optional[TechnologySpec]:
    return TECHNOLOGY_CATALOG.get(key)


def technology_from_label(label: str) -> Optional[str]:
    for ui_label, key in UI_TECHNOLOGY_OPTIONS:
        if ui_label == label or key == label:
            return key
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


def _technology_entry(key: str, spec: TechnologySpec) -> Dict[str, Any]:
    caps = _PLATFORM_CAPABILITIES.get(key, {})
    return {
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
    }


TECHNOLOGIES: Dict[str, Dict[str, Any]] = {
    key: _technology_entry(key, spec) for key, spec in TECHNOLOGY_CATALOG.items()
}


def list_technologies() -> List[str]:
    return list(TECHNOLOGY_CATALOG.keys())
