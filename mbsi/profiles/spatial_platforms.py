"""Per-platform Seurat-like workflow dicts for all 9 MBSI platforms."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mbsi.schema.technology import TECHNOLOGY_CATALOG, list_technologies

_COMPATIBLE_MODULES = ["qc_preprocess", "spatial_analysis", "discovery", "report_export"]


def _platform_workflow(key: str) -> Dict[str, Any]:
    spec = TECHNOLOGY_CATALOG[key]
    return {
        "platform": key,
        "display_name": spec.label,
        "required_files": list(spec.required_files),
        "optional_files": [],
        "qc_metrics": list(spec.qc_metrics),
        "normalization_options": _normalization_options(key, spec.normalization_strategy),
        "segmentation_strategy": spec.segmentation_logic,
        "clustering_options": list(spec.clustering_choices) or ["Leiden", "Louvain"],
        "benchmark_eligibility": spec.benchmark_eligibility,
        "compatible_modules": list(_COMPATIBLE_MODULES),
        "default_preset": _default_preset(key),
    }


def _normalization_options(key: str, strategy: str) -> List[str]:
    base = ["log1p", "sctransform_like"]
    if key in ("codex",):
        return ["arcsinh", "percentile", "log1p"]
    if key == "spatial_atac":
        return ["tf_idf", "log1p", "sctransform_like"]
    if "SCTransform" in strategy:
        return ["sctransform_like", "log1p"] + base
    return base


def _default_preset(key: str) -> str:
    mapping = {
        "visium": "spatial_transcriptomics",
        "visium_hd": "visium_hd",
        "xenium": "imaging_based_spatial",
        "cosmx": "imaging_based_spatial",
        "merfish": "imaging_based_spatial",
        "codex": "imaging_based_spatial",
        "stereo_seq": "spatial_transcriptomics",
        "spatial_atac": "scrna_scatac_integration",
        "generic_h5ad": "basic_unsupervised",
    }
    return mapping.get(key, "basic_unsupervised")


SPATIAL_PLATFORM_WORKFLOWS: Dict[str, Dict[str, Any]] = {
    key: _platform_workflow(key) for key in list_technologies()
}


def get_platform_workflow(platform: str) -> Dict[str, Any]:
    return dict(SPATIAL_PLATFORM_WORKFLOWS.get(platform, SPATIAL_PLATFORM_WORKFLOWS["generic_h5ad"]))


def list_platform_workflows() -> List[str]:
    return list(SPATIAL_PLATFORM_WORKFLOWS.keys())
