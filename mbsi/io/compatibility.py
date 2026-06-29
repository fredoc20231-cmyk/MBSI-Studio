"""Module compatibility matrix from ingested AnnData and schema."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import anndata as ad

from mbsi.io.detect import PlatformDetection
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WorkflowModule

PLATFORM_MODULE_RULES: Dict[str, Dict[str, bool]] = {
    "stereo_seq": {
        "qc_preprocess": True,
        "segment_register": True,
        "spatial_analysis": True,
        "reconstruction": True,
        "discovery": True,
        "ai_review": True,
        "report_export": True,
    },
}


def _entry(status: str, reason: str = "", required_missing: Optional[List[str]] = None, recommended_next_step: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {"status": status, "reason": reason}
    if required_missing:
        out["required_missing"] = list(required_missing)
    if recommended_next_step:
        out["recommended_next_step"] = recommended_next_step
    return out


def recommended_next_step_for_module(
    module_key: str,
    status: str,
    required_missing: Optional[List[str]] = None,
    has_adata: bool = False,
) -> str:
    """Human-readable next step for compatibility matrix rows."""
    missing = required_missing or []
    if not has_adata and module_key not in (
        WorkflowModule.STUDY_SETUP.value,
        WorkflowModule.REPORT_EXPORT.value,
        WorkflowModule.SETTINGS.value,
        WorkflowModule.AI_REVIEW.value,
    ):
        return "Upload spatial omics data in Study Setup"
    if status == "available":
        labels = {
            WorkflowModule.QC_PREPROCESS.value: "Continue to Data QC & Preprocessing",
            WorkflowModule.SEGMENT_REGISTER.value: "Run segmentation & registration",
            WorkflowModule.SPATIAL_ANALYSIS.value: "Run spatial analysis",
            WorkflowModule.RECONSTRUCTION.value: "Run MBSI reconstruction",
            WorkflowModule.BENCHMARK.value: "Run benchmark with ground truth",
            WorkflowModule.DISCOVERY.value: "Run Discovery Intelligence",
            WorkflowModule.AI_REVIEW.value: "Review findings in AI Review",
            WorkflowModule.REPORT_EXPORT.value: "Generate final report",
        }
        return labels.get(module_key, "Proceed with this module")
    if missing:
        return f"Resolve: {missing[0]}"
    if status == "warn":
        return "Proceed with caution — review warnings first"
    return "Complete prerequisites in Study Setup"


def _stereo_benchmark_available(adata: ad.AnnData, detection: Optional[PlatformDetection]) -> bool:
    stereo = adata.uns.get("stereo_seq", {})
    cell_boundaries = "cell_id" in adata.obs or stereo.get("cgef") or stereo.get("segmentation")
    segmentation_present = bool(stereo.get("segmentation")) or "segmentation" in adata.uns
    external_gt = adata.uns.get("single_cell_reference") is not None
    return bool(cell_boundaries or segmentation_present or external_gt)


def get_platform_module_rules(platform: str) -> Dict[str, bool]:
    """Return technology-specific module availability flags."""
    return dict(PLATFORM_MODULE_RULES.get(platform, {}))


def _add_legacy_aliases(matrix: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    matrix["upload"] = matrix[WorkflowModule.STUDY_SETUP.value]
    matrix["qc"] = matrix[WorkflowModule.QC_PREPROCESS.value]
    matrix["spatial_analysis"] = matrix[WorkflowModule.SPATIAL_ANALYSIS.value]
    matrix["mbsi_reconstruction"] = matrix[WorkflowModule.RECONSTRUCTION.value]
    matrix["benchmark_hub"] = matrix[WorkflowModule.BENCHMARK.value]
    matrix["communication"] = matrix[WorkflowModule.DISCOVERY.value]
    matrix["tme"] = matrix[WorkflowModule.DISCOVERY.value]
    matrix["discovery"] = matrix[WorkflowModule.DISCOVERY.value]
    matrix["report"] = matrix[WorkflowModule.REPORT_EXPORT.value]
    return matrix


def get_compatibility_matrix(
    adata: Optional[ad.AnnData],
    detection: Optional[PlatformDetection] = None,
    technology_key: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Return per-workflow-module availability based on data contract and technology catalog."""
    tech_key = technology_key or (detection or {}).get("technology_key") or (detection or {}).get("platform")
    tech = get_technology(tech_key) if tech_key else None
    compatible = set(tech.compatible_analyses) if tech else set()

    if adata is None:
        matrix = {
            WorkflowModule.STUDY_SETUP.value: _entry("available"),
            WorkflowModule.QC_PREPROCESS.value: _entry("unavailable", "no data loaded", ["spatial omics upload"]),
            WorkflowModule.SEGMENT_REGISTER.value: _entry("unavailable", "no data loaded", ["spatial omics upload"]),
            WorkflowModule.SPATIAL_ANALYSIS.value: _entry("unavailable", "no data loaded", ["spatial omics upload"]),
            WorkflowModule.RECONSTRUCTION.value: _entry("unavailable", "no data loaded", ["spatial omics upload"]),
            WorkflowModule.BENCHMARK.value: _entry("unavailable", "no data loaded", ["spatial omics upload"]),
            WorkflowModule.DISCOVERY.value: _entry(
                "unavailable",
                "upload real spatial data first",
                ["spatial omics upload"],
                "Upload data in Study Setup before Discovery",
            ),
            WorkflowModule.AI_REVIEW.value: _entry("warn", "run discovery or analysis first"),
            WorkflowModule.REPORT_EXPORT.value: _entry("available"),
            WorkflowModule.SETTINGS.value: _entry("available"),
        }
        return _add_legacy_aliases(matrix)

    has_spatial = "spatial" in adata.obsm
    n_obs = adata.n_obs
    n_vars = adata.n_vars
    has_cell_types = "cell_type" in adata.obs or "cluster" in adata.obs
    platform = tech_key or (detection or {}).get("platform") or adata.uns.get("mbsi_platform", "unknown")
    has_sc_ref = adata.uns.get("single_cell_reference") is not None
    platform_rules = get_platform_module_rules(platform)
    partial = bool((detection or {}).get("partial_support"))

    benchmark_available = has_sc_ref
    if platform == "stereo_seq":
        benchmark_available = _stereo_benchmark_available(adata, detection)

    missing_spatial: List[str] = [] if has_spatial else ["spatial coordinates in obsm['spatial']"]
    missing_genes: List[str] = [] if n_vars >= 20 else ["sufficient gene features (≥20)"]

    matrix = {
        WorkflowModule.STUDY_SETUP.value: _entry("available"),
        WorkflowModule.QC_PREPROCESS.value: _entry(
            "available" if has_spatial and n_obs >= 5 else "unavailable",
            "needs spatial coords and minimum spot count",
            missing_spatial or (["minimum 5 observations"] if n_obs < 5 else None),
        ),
        WorkflowModule.SEGMENT_REGISTER.value: _entry(
            "available" if has_spatial else "warn",
            "segmentation improves with histology or platform masks",
            missing_spatial or None,
        ),
        WorkflowModule.SPATIAL_ANALYSIS.value: _entry(
            "available" if has_spatial and n_vars >= 20 else "warn",
            "low gene count or missing spatial coords",
            (missing_spatial + missing_genes) or None,
        ),
        WorkflowModule.RECONSTRUCTION.value: _entry(
            "available" if has_spatial and n_obs >= 20 else "warn",
            "reconstruction works best with ≥20 spots",
            missing_spatial or (["≥20 spots recommended"] if n_obs < 20 else None),
        ),
        WorkflowModule.BENCHMARK.value: _entry(
            "unavailable" if not benchmark_available else "available",
            "requires single-cell ground truth reference"
            if not benchmark_available
            else "ground truth or Stereo-seq segmentation available",
            [] if benchmark_available else ["ground-truth reference h5ad"],
        ),
        WorkflowModule.DISCOVERY.value: _entry(
            "warn" if platform in ("unknown", "incomplete") or partial else "available",
            "discovery requires uploaded spatial data with gene expression",
            None if has_spatial and n_vars >= 20 else missing_spatial + missing_genes,
            "Run Discovery Intelligence after QC" if has_spatial else "Upload spatial omics data first",
        ),
        WorkflowModule.AI_REVIEW.value: _entry("available", "Available after pipeline findings are generated"),
        WorkflowModule.REPORT_EXPORT.value: _entry("available"),
        WorkflowModule.SETTINGS.value: _entry("available"),
    }

    if platform == "stereo_seq" and platform_rules:
        if not platform_rules.get("reconstruction"):
            matrix[WorkflowModule.RECONSTRUCTION.value] = _entry("warn", "limited at ultra-high resolution")
        if platform_rules.get("segmentation") and adata.uns.get("stereo_seq", {}).get("segmentation"):
            matrix[WorkflowModule.DISCOVERY.value] = _entry("available", "ultra-high-resolution discovery enabled")

    if tech and compatible:
        for mod_key in [m.value for m in WorkflowModule]:
            if mod_key in (
                WorkflowModule.STUDY_SETUP.value,
                WorkflowModule.SETTINGS.value,
                WorkflowModule.REPORT_EXPORT.value,
            ):
                continue
            if mod_key not in compatible and matrix[mod_key]["status"] == "available":
                matrix[mod_key] = _entry(
                    "warn",
                    f"{tech.label} has limited support for this module",
                    [f"technology {tech.key} compatibility"],
                )

    return _add_legacy_aliases(matrix)
