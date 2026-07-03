"""Module compatibility matrix from ingested AnnData and schema."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import anndata as ad

from mbsi.io.detect import PlatformDetection
from mbsi.schema.technology import get_technology, is_milestone_platform
from mbsi.schema.workflow import WorkflowModule

MILESTONE_MODULE_KEYS = [
    WorkflowModule.STUDY_DATA.value,
    WorkflowModule.QC_TRANSFORMATION.value,
    WorkflowModule.VISUALIZATION.value,
    WorkflowModule.SPATIAL_VARIABLE_GENES.value,
    WorkflowModule.SPATIAL_DOMAINS.value,
    WorkflowModule.PHENOTYPING.value,
    WorkflowModule.REPORT_EXPORT.value,
]

PLATFORM_MODULE_RULES: Dict[str, Dict[str, bool]] = {
    "visium": {key: True for key in MILESTONE_MODULE_KEYS},
    "xenium": {key: True for key in MILESTONE_MODULE_KEYS},
    "generic_h5ad": {key: True for key in MILESTONE_MODULE_KEYS},
    "csv_matrix": {key: True for key in MILESTONE_MODULE_KEYS},
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
        WorkflowModule.AI_REVIEW.value,
    ):
        return "Upload spatial omics data in Study Setup"
    if status == "available":
        labels = {
            WorkflowModule.QC_TRANSFORMATION.value: "Continue to QC & Transformation",
            WorkflowModule.QC_PREPROCESS.value: "Continue to QC & Transformation",
            WorkflowModule.VISUALIZATION.value: "Run visualization and clustering",
            WorkflowModule.SPATIAL_ANALYSIS.value: "Run visualization and clustering",
            WorkflowModule.SPATIAL_VARIABLE_GENES.value: "Run spatial variable gene analysis",
            WorkflowModule.SPATIAL_DOMAINS.value: "Detect spatial domains",
            WorkflowModule.PHENOTYPING.value: "Run basic phenotyping",
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
    matrix["upload"] = matrix[WorkflowModule.STUDY_DATA.value]
    matrix["qc"] = matrix[WorkflowModule.QC_TRANSFORMATION.value]
    matrix["spatial_analysis"] = matrix[WorkflowModule.VISUALIZATION.value]
    matrix["mbsi_reconstruction"] = matrix.get(
        WorkflowModule.RECONSTRUCTION.value,
        _entry("warn", "out of Milestone 1 scope"),
    )
    matrix["benchmark_hub"] = matrix.get(
        WorkflowModule.BENCHMARK.value,
        _entry("unavailable", "out of Milestone 1 scope"),
    )
    matrix["communication"] = matrix.get(
        WorkflowModule.DISCOVERY.value,
        _entry("warn", "out of Milestone 1 scope"),
    )
    matrix["tme"] = matrix.get(
        WorkflowModule.DISCOVERY.value,
        _entry("warn", "out of Milestone 1 scope"),
    )
    matrix["discovery"] = matrix.get(
        WorkflowModule.DISCOVERY.value,
        _entry(
            "unavailable",
            "discovery requires uploaded spatial data with gene expression",
            recommended_next_step="Upload spatial omics data to enable discovery.",
        ),
    )
    matrix["report"] = matrix[WorkflowModule.REPORT_EXPORT.value]
    return matrix


def _milestone_module_status(
    module_key: str,
    *,
    has_spatial: bool,
    n_obs: int,
    n_vars: int,
    has_cluster: bool,
    platform: str,
) -> Dict[str, Any]:
    """Readiness for Milestone 1 workflow modules (Visium / Xenium / generic)."""
    missing_spatial: List[str] = [] if has_spatial else ["spatial coordinates in obsm['spatial']"]
    missing_genes: List[str] = [] if n_vars >= 20 else ["sufficient gene features (≥20)"]
    missing_obs: List[str] = [] if n_obs >= 5 else ["minimum 5 observations"]

    if module_key == WorkflowModule.STUDY_DATA.value:
        return _entry("available")
    if module_key == WorkflowModule.QC_TRANSFORMATION.value:
        return _entry(
            "available" if has_spatial and n_obs >= 5 else "unavailable",
            "needs spatial coords and minimum observation count",
            missing_spatial or missing_obs or None,
        )
    if module_key == WorkflowModule.VISUALIZATION.value:
        return _entry(
            "available" if has_spatial and n_vars >= 20 else "warn",
            "visualization needs spatial coords and ≥20 genes",
            (missing_spatial + missing_genes) or None,
        )
    if module_key == WorkflowModule.SPATIAL_VARIABLE_GENES.value:
        return _entry(
            "available" if has_spatial and n_vars >= 20 and n_obs >= 10 else "warn",
            "SVG analysis needs spatial coords and sufficient genes/cells",
            (missing_spatial + missing_genes) or None,
        )
    if module_key == WorkflowModule.SPATIAL_DOMAINS.value:
        return _entry(
            "available" if has_spatial and n_obs >= 10 else "warn",
            "domain detection needs spatial coords and ≥10 observations",
            missing_spatial or (["≥10 observations recommended"] if n_obs < 10 else None),
        )
    if module_key == WorkflowModule.PHENOTYPING.value:
        status = "available" if has_spatial and n_vars >= 5 else "warn"
        return _entry(status, "phenotyping uses expression and optional cluster labels", missing_genes or None)
    if module_key == WorkflowModule.REPORT_EXPORT.value:
        note = "export after QC/visualization recommended" if not has_cluster else "ready for export"
        return _entry("available", note)
    return _entry("warn", f"module {module_key} not in milestone scope")


def get_compatibility_matrix(
    adata: Optional[ad.AnnData],
    detection: Optional[PlatformDetection] = None,
    technology_key: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Return per-workflow-module availability based on data contract and technology catalog."""
    tech_key = technology_key or (detection or {}).get("technology_key") or (detection or {}).get("platform")
    tech = get_technology(tech_key) if tech_key else None
    compatible = set(tech.compatible_analyses) if tech else set()
    platform = tech_key or (detection or {}).get("platform") or "unknown"
    milestone_platform = is_milestone_platform(platform) or platform == "csv_matrix"

    if adata is None:
        matrix = {key: _entry("unavailable", "no data loaded", ["spatial omics upload"]) for key in MILESTONE_MODULE_KEYS}
        matrix[WorkflowModule.STUDY_DATA.value] = _entry("available")
        matrix[WorkflowModule.REPORT_EXPORT.value] = _entry("available")
        matrix[WorkflowModule.SETTINGS.value] = _entry("available")
        matrix[WorkflowModule.QC_PREPROCESS.value] = matrix[WorkflowModule.QC_TRANSFORMATION.value]
        matrix[WorkflowModule.SPATIAL_ANALYSIS.value] = matrix[WorkflowModule.VISUALIZATION.value]
        return _add_legacy_aliases(matrix)

    has_spatial = "spatial" in adata.obsm
    n_obs = adata.n_obs
    n_vars = adata.n_vars
    has_cell_types = "cell_type" in adata.obs or "cluster" in adata.obs
    platform = tech_key or (detection or {}).get("platform") or adata.uns.get("mbsi_platform", "unknown")
    if not is_milestone_platform(platform) and platform not in ("csv_matrix", "unknown", "incomplete"):
        tech = get_technology(platform)
        label = tech.label if tech else platform
        reason = f"{label} is Coming later in Milestone 1 — select Visium, Xenium, or Generic h5ad/CSV"
        matrix = {
            key: _entry("coming_later", reason, [f"technology {platform} not in Milestone 1 scope"])
            for key in MILESTONE_MODULE_KEYS
        }
        matrix[WorkflowModule.STUDY_DATA.value] = _entry("available", "Study setup always available")
        matrix[WorkflowModule.REPORT_EXPORT.value] = _entry("coming_later", reason)
        matrix[WorkflowModule.SETTINGS.value] = _entry("available")
        matrix[WorkflowModule.QC_PREPROCESS.value] = matrix[WorkflowModule.QC_TRANSFORMATION.value]
        matrix[WorkflowModule.SPATIAL_ANALYSIS.value] = matrix[WorkflowModule.VISUALIZATION.value]
        return _add_legacy_aliases(matrix)

    has_sc_ref = adata.uns.get("single_cell_reference") is not None
    platform_rules = get_platform_module_rules(platform)
    partial = bool((detection or {}).get("partial_support"))
    has_cluster = "cluster" in adata.obs or "domain" in adata.obs

    if milestone_platform:
        matrix = {
            key: _milestone_module_status(
                key,
                has_spatial=has_spatial,
                n_obs=n_obs,
                n_vars=n_vars,
                has_cluster=has_cluster,
                platform=platform,
            )
            for key in MILESTONE_MODULE_KEYS
        }
        matrix[WorkflowModule.SETTINGS.value] = _entry("available")
        matrix[WorkflowModule.QC_PREPROCESS.value] = matrix[WorkflowModule.QC_TRANSFORMATION.value]
        matrix[WorkflowModule.SPATIAL_ANALYSIS.value] = matrix[WorkflowModule.VISUALIZATION.value]
        if tech and compatible:
            for mod_key in MILESTONE_MODULE_KEYS:
                if mod_key not in compatible and matrix[mod_key]["status"] == "available":
                    matrix[mod_key] = _entry("warn", f"{tech.label} has limited support for this module")
        return _add_legacy_aliases(matrix)

    benchmark_available = has_sc_ref
    if platform == "stereo_seq":
        benchmark_available = _stereo_benchmark_available(adata, detection)

    missing_spatial: List[str] = [] if has_spatial else ["spatial coordinates in obsm['spatial']"]
    missing_genes: List[str] = [] if n_vars >= 20 else ["sufficient gene features (≥20)"]

    matrix = {
        WorkflowModule.STUDY_DATA.value: _entry("available"),
        WorkflowModule.QC_TRANSFORMATION.value: _entry(
            "available" if has_spatial and n_obs >= 5 else "unavailable",
            "needs spatial coords and minimum spot count",
            missing_spatial or (["minimum 5 observations"] if n_obs < 5 else None),
        ),
        WorkflowModule.QC_PREPROCESS.value: _entry(
            "available" if has_spatial and n_obs >= 5 else "unavailable",
            "needs spatial coords and minimum spot count",
            missing_spatial or (["minimum 5 observations"] if n_obs < 5 else None),
        ),
        WorkflowModule.VISUALIZATION.value: _entry(
            "available" if has_spatial and n_vars >= 20 else "warn",
            "low gene count or missing spatial coords",
            (missing_spatial + missing_genes) or None,
        ),
        WorkflowModule.SPATIAL_ANALYSIS.value: _entry(
            "available" if has_spatial and n_vars >= 20 else "warn",
            "low gene count or missing spatial coords",
            (missing_spatial + missing_genes) or None,
        ),
        WorkflowModule.SEGMENT_REGISTER.value: _entry(
            "available" if has_spatial else "warn",
            "segmentation improves with histology or platform masks",
            missing_spatial or None,
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
            if mod_key not in compatible and matrix.get(mod_key, {}).get("status") == "available":
                matrix[mod_key] = _entry(
                    "warn",
                    f"{tech.label} has limited support for this module",
                    [f"technology {tech.key} compatibility"],
                )

    return _add_legacy_aliases(matrix)
