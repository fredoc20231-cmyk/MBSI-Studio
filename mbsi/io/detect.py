"""
Platform auto-detection for spatial transcriptomics data.

Given a set of uploaded file names and/or a directory, identifies which
spatial omics platform the data comes from and what is present vs missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Platform definitions
# ---------------------------------------------------------------------------

@dataclass
class PlatformSpec:
    name: str
    display_name: str
    required: List[str]          # file name patterns (case-insensitive)
    optional: List[str]
    coordinate_type: str         # "spot" | "cell" | "molecule"
    resolution: str              # "spot" | "single-cell" | "subcellular"
    description: str


PLATFORM_SPECS: List[PlatformSpec] = [
    PlatformSpec(
        name="visium",
        display_name="10x Visium / Visium HD",
        required=["filtered_feature_bc_matrix.h5", "tissue_positions"],
        optional=[
            "tissue_hires_image.png", "tissue_lowres_image.png",
            "scalefactors_json.json", "raw_feature_bc_matrix.h5",
        ],
        coordinate_type="spot",
        resolution="spot",
        description="55 µm capture spots, ~3–15 cells per spot",
    ),
    PlatformSpec(
        name="xenium",
        display_name="10x Xenium",
        required=["cell_feature_matrix.h5", "cells.csv"],
        optional=[
            "transcripts.csv", "transcripts.parquet",
            "cells.parquet", "nucleus_boundaries.csv",
            "cell_boundaries.csv", "morphology_focus.ome.tif",
            "morphology.ome.tif",
        ],
        coordinate_type="cell",
        resolution="single-cell",
        description="Single-cell in-situ sequencing with subcellular transcripts",
    ),
    PlatformSpec(
        name="merfish",
        display_name="MERFISH / MERSCOPE",
        required=["cell_by_gene.csv", "cell_metadata.csv"],
        optional=[
            "detected_transcripts.csv", "cell_boundaries.parquet",
            "images", "z_slices",
        ],
        coordinate_type="cell",
        resolution="single-cell",
        description="Multiplexed error-robust FISH, subcellular resolution",
    ),
    PlatformSpec(
        name="cosmx",
        display_name="NanoString CosMx",
        required=["exprMat_file", "metadata_file"],
        optional=[
            "fov_positions_file", "CellComposite", "CellLabels",
            "tx_file", "polygons",
        ],
        coordinate_type="cell",
        resolution="single-cell",
        description="Single-cell spatial proteogenomics, ~1000 gene panel",
    ),
    PlatformSpec(
        name="codex",
        display_name="CODEX / PhenoCycler",
        required=["cell_table", "channel_names"],
        optional=["ome.tif", "cell_masks", "region_masks"],
        coordinate_type="cell",
        resolution="single-cell",
        description="Multiplexed protein imaging, cyclic immunofluorescence",
    ),
    PlatformSpec(
        name="slideseq",
        display_name="Slide-seq / Slide-seqV2",
        required=["barcodes.txt", "BeadLocationsForR.csv"],
        optional=["digital_expression.txt"],
        coordinate_type="spot",
        resolution="spot",
        description="10 µm bead-based spatial sequencing",
    ),
    PlatformSpec(
        name="stereoseq",
        display_name="Stereo-seq",
        required=[".gem", ".gef"],
        optional=["tissue_cut.tif"],
        coordinate_type="spot",
        resolution="spot",
        description="DNB-based spatial transcriptomics at nanoscale resolution",
    ),
    PlatformSpec(
        name="h5ad",
        display_name="Generic AnnData (h5ad)",
        required=[".h5ad"],
        optional=[],
        coordinate_type="cell",
        resolution="single-cell",
        description="Standard AnnData format with spatial coordinates in obsm['spatial']",
    ),
    PlatformSpec(
        name="csv",
        display_name="Generic CSV Matrix + Coordinates",
        required=[".csv"],
        optional=[".png", ".tif", ".tiff"],
        coordinate_type="cell",
        resolution="single-cell",
        description="Count matrix CSV with paired spatial coordinates CSV",
    ),
]

PLATFORM_BY_NAME: Dict[str, PlatformSpec] = {p.name: p for p in PLATFORM_SPECS}


# ---------------------------------------------------------------------------
# Detection result
# ---------------------------------------------------------------------------

@dataclass
class DetectionResult:
    platform: Optional[str]           # platform name or None
    display_name: str
    confidence: float                 # 0–1
    files_found: List[str]
    files_missing: List[str]
    files_optional_found: List[str]
    files_optional_missing: List[str]
    warnings: List[str] = field(default_factory=list)
    notes: str = ""

    @property
    def is_known_platform(self) -> bool:
        return self.platform is not None and self.platform not in ("h5ad", "csv", "unknown")

    @property
    def coordinate_type(self) -> str:
        if self.platform and self.platform in PLATFORM_BY_NAME:
            return PLATFORM_BY_NAME[self.platform].coordinate_type
        return "unknown"

    @property
    def resolution(self) -> str:
        if self.platform and self.platform in PLATFORM_BY_NAME:
            return PLATFORM_BY_NAME[self.platform].resolution
        return "unknown"


# ---------------------------------------------------------------------------
# Compatibility matrix
# ---------------------------------------------------------------------------

ANALYSIS_REQUIREMENTS: Dict[str, Dict] = {
    "QC": {
        "requires": ["expression_matrix", "spatial_coords"],
        "description": "Quality control plots and metrics",
    },
    "Spatial Analysis": {
        "requires": ["expression_matrix", "spatial_coords"],
        "description": "PCA, UMAP, clusters, spatial statistics",
    },
    "MBSI Reconstruction": {
        "requires": ["expression_matrix", "spatial_coords"],
        "needs_spot_data": True,
        "description": "Physics-aware super-resolution reconstruction",
    },
    "Communication": {
        "requires": ["expression_matrix", "spatial_coords", "gene_names"],
        "description": "Ligand-receptor interaction analysis",
    },
    "TME Intelligence": {
        "requires": ["expression_matrix", "spatial_coords", "cell_types"],
        "description": "Tumor microenvironment niche analysis",
    },
    "Benchmark Hub": {
        "requires": ["expression_matrix", "spatial_coords", "ground_truth"],
        "description": "Reconstruction validation against single-cell ground truth",
        "unavailable_without": "ground_truth",
        "unavailable_msg": "Requires Xenium/CosMx/MERFISH single-cell reference",
    },
    "Discovery Engine": {
        "requires": ["expression_matrix", "spatial_coords"],
        "description": "Causal drivers, biomarker candidates, perturbation hypotheses",
    },
    "Digital Twin": {
        "requires": ["expression_matrix", "spatial_coords"],
        "description": "In-silico treatment simulation",
    },
    "Report": {
        "requires": ["expression_matrix"],
        "description": "Comprehensive analysis report",
    },
}


def compute_compatibility_matrix(
    adata_present: bool,
    has_spatial: bool,
    has_gene_names: bool,
    has_cell_types: bool,
    has_ground_truth: bool,
    is_spot_platform: bool,
) -> Dict[str, Dict]:
    """Return per-analysis availability status."""
    flags = {
        "expression_matrix": adata_present,
        "spatial_coords": has_spatial,
        "gene_names": has_gene_names,
        "cell_types": has_cell_types,
        "ground_truth": has_ground_truth,
    }

    matrix = {}
    for analysis, spec in ANALYSIS_REQUIREMENTS.items():
        missing = [r for r in spec["requires"] if not flags.get(r, False)]
        mbsi_ok = not spec.get("needs_spot_data", False) or is_spot_platform

        if missing or not mbsi_ok:
            reason_parts = []
            if missing:
                reason_parts.append(f"Missing: {', '.join(missing)}")
            if not mbsi_ok:
                reason_parts.append("MBSI reconstruction requires spot-level data (Visium/Slide-seq)")
            unavail_msg = spec.get("unavailable_msg", "; ".join(reason_parts))
            matrix[analysis] = {"available": False, "reason": unavail_msg}
        else:
            matrix[analysis] = {"available": True, "reason": spec["description"]}

    return matrix


# ---------------------------------------------------------------------------
# Detection logic
# ---------------------------------------------------------------------------

def _normalise(name: str) -> str:
    return name.lower().replace(" ", "_")


def _files_match(file_names: Set[str], patterns: List[str]) -> List[str]:
    """Return subset of patterns that match at least one file name."""
    matched = []
    for pat in patterns:
        pat_low = pat.lower()
        if any(pat_low in f.lower() for f in file_names):
            matched.append(pat)
    return matched


def detect_platform(file_names: List[str]) -> DetectionResult:
    """
    Identify the spatial omics platform from a list of file names.

    Parameters
    ----------
    file_names : list of str
        File names present (from ZIP extraction or directory listing).

    Returns
    -------
    DetectionResult
    """
    name_set = {Path(f).name for f in file_names}
    name_set_lower = {n.lower() for n in name_set}
    all_lower = {f.lower() for f in file_names}

    best_spec: Optional[PlatformSpec] = None
    best_score = -1.0
    best_req_found: List[str] = []
    best_req_missing: List[str] = []
    best_opt_found: List[str] = []
    best_opt_missing: List[str] = []

    for spec in PLATFORM_SPECS:
        req_found = _files_match(all_lower | name_set_lower, spec.required)
        req_missing = [r for r in spec.required if r not in req_found]
        opt_found = _files_match(all_lower | name_set_lower, spec.optional)
        opt_missing = [o for o in spec.optional if o not in opt_found]

        if not spec.required:
            score = 0.0
        else:
            score = len(req_found) / len(spec.required)

        if score > best_score:
            best_score = score
            best_spec = spec
            best_req_found = req_found
            best_req_missing = req_missing
            best_opt_found = opt_found
            best_opt_missing = opt_missing

    if best_spec is None or best_score == 0:
        return DetectionResult(
            platform="unknown",
            display_name="Unknown / Unrecognised",
            confidence=0.0,
            files_found=[],
            files_missing=[],
            files_optional_found=[],
            files_optional_missing=[],
            warnings=["Could not identify platform from file names."],
        )

    return DetectionResult(
        platform=best_spec.name,
        display_name=best_spec.display_name,
        confidence=best_score,
        files_found=best_req_found,
        files_missing=best_req_missing,
        files_optional_found=best_opt_found,
        files_optional_missing=best_opt_missing,
        notes=best_spec.description,
    )
