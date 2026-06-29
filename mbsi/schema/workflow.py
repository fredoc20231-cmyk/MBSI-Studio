"""Workflow module definitions — 10 canonical workspace modules."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List


class WorkflowModule(str, Enum):
    STUDY_SETUP = "study_setup"
    QC_PREPROCESS = "qc_preprocess"
    SEGMENT_REGISTER = "segment_register"
    SPATIAL_ANALYSIS = "spatial_analysis"
    RECONSTRUCTION = "reconstruction"
    BENCHMARK = "benchmark"
    DISCOVERY = "discovery"
    AI_REVIEW = "ai_review"
    REPORT_EXPORT = "report_export"
    SETTINGS = "settings"


WORKFLOW_MODULE_LABELS: Dict[str, str] = {
    WorkflowModule.STUDY_SETUP.value: "Study Setup & Data Ingestion",
    WorkflowModule.QC_PREPROCESS.value: "Data QC & Preprocessing",
    WorkflowModule.SEGMENT_REGISTER.value: "Segmentation & Registration",
    WorkflowModule.SPATIAL_ANALYSIS.value: "Spatial Analysis",
    WorkflowModule.RECONSTRUCTION.value: "MBSI Reconstruction",
    WorkflowModule.BENCHMARK.value: "Benchmark & Validation",
    WorkflowModule.DISCOVERY.value: "Discovery Intelligence",
    WorkflowModule.AI_REVIEW.value: "AI Review & Evidence",
    WorkflowModule.REPORT_EXPORT.value: "Report & Export",
    WorkflowModule.SETTINGS.value: "Admin / Settings",
}

WORKFLOW_SUBSTEPS: Dict[str, List[str]] = {
    WorkflowModule.STUDY_SETUP.value: [
        "technology_selection",
        "project_description",
        "experimental_design",
        "sample_table",
        "file_upload",
        "reference_markers",
        "readiness_compatibility",
    ],
    WorkflowModule.QC_PREPROCESS.value: [
        "qc_thresholds",
        "normalization",
        "batch_replicate",
        "mito_ribo",
        "filtering",
        "platform_qc",
        "statistical_criteria",
    ],
    WorkflowModule.SEGMENT_REGISTER.value: [
        "tissue_segmentation",
        "cell_segmentation",
        "image_registration",
        "region_selection",
    ],
    WorkflowModule.SPATIAL_ANALYSIS.value: [
        "pca_umap",
        "clustering",
        "marker_genes",
        "morans_i",
        "spatially_variable_genes",
        "neighborhood_analysis",
    ],
    WorkflowModule.RECONSTRUCTION.value: [
        "solver_config",
        "transport_map",
        "cell_assignment",
        "validation_metrics",
    ],
    WorkflowModule.BENCHMARK.value: [
        "reference_selection",
        "method_comparison",
        "metrics_dashboard",
        "validation_report",
    ],
    WorkflowModule.DISCOVERY.value: [
        "communication",
        "tme_niches",
        "immune_exclusion",
        "caf_barriers",
        "tls",
        "hypoxia",
        "angiogenesis",
        "invasion_fronts",
        "biomarkers",
        "causal_drivers",
        "validation_recommendations",
    ],
    WorkflowModule.AI_REVIEW.value: [
        "grounded_qa",
        "evidence_browser",
        "confidence_review",
    ],
    WorkflowModule.REPORT_EXPORT.value: [
        "results_notebook",
        "html_report",
        "pdf_export",
        "data_bundle",
        "download_center",
    ],
    WorkflowModule.SETTINGS.value: [
        "session",
        "theme",
        "export_defaults",
    ],
}

# Legacy module key mapping for session state / redirects
LEGACY_MODULE_MAP: Dict[str, str] = {
    "project_setup": WorkflowModule.STUDY_SETUP.value,
    "project": WorkflowModule.STUDY_SETUP.value,
    "upload": WorkflowModule.STUDY_SETUP.value,
    "preprocess": WorkflowModule.QC_PREPROCESS.value,
    "segmentation": WorkflowModule.SEGMENT_REGISTER.value,
    "communication": WorkflowModule.DISCOVERY.value,
    "tme": WorkflowModule.DISCOVERY.value,
    "ml_learning": WorkflowModule.SETTINGS.value,
    "notebook": WorkflowModule.REPORT_EXPORT.value,
    "report": WorkflowModule.REPORT_EXPORT.value,
}


def resolve_module_key(key: str) -> str:
    return LEGACY_MODULE_MAP.get(key, key)
