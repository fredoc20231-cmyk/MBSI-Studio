"""Workflow module definitions — 16 canonical workspace modules."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List


class WorkflowModule(str, Enum):
    STUDY_DATA = "study_data"
    QC_TRANSFORMATION = "qc_transformation"
    VISUALIZATION = "visualization"
    SPATIAL_VARIABLE_GENES = "spatial_variable_genes"
    SPATIAL_GENE_SETS = "spatial_gene_sets"
    SPATIAL_DOMAINS = "spatial_domains"
    PHENOTYPING = "phenotyping"
    DIFFERENTIAL_ANALYSIS = "differential_analysis"
    SPATIAL_GRADIENTS = "spatial_gradients"
    SEGMENT_REGISTER = "segment_register"
    RECONSTRUCTION = "reconstruction"
    BENCHMARK = "benchmark"
    DISCOVERY = "discovery"
    AI_REVIEW = "ai_review"
    REPORT_EXPORT = "report_export"
    SETTINGS = "settings"

    # Legacy aliases (resolve to canonical keys)
    STUDY_SETUP = "study_data"
    QC_PREPROCESS = "qc_transformation"
    SPATIAL_ANALYSIS = "visualization"


WORKFLOW_MODULE_LABELS: Dict[str, str] = {
    WorkflowModule.STUDY_DATA.value: "Study & Data",
    WorkflowModule.QC_TRANSFORMATION.value: "QC & Transformation",
    WorkflowModule.VISUALIZATION.value: "Visualization",
    WorkflowModule.SPATIAL_VARIABLE_GENES.value: "Spatial Variable Genes",
    WorkflowModule.SPATIAL_GENE_SETS.value: "Spatial Gene Sets",
    WorkflowModule.SPATIAL_DOMAINS.value: "Spatial Domains",
    WorkflowModule.PHENOTYPING.value: "Phenotyping",
    WorkflowModule.DIFFERENTIAL_ANALYSIS.value: "Differential Analysis",
    WorkflowModule.SPATIAL_GRADIENTS.value: "Spatial Gradients",
    WorkflowModule.SEGMENT_REGISTER.value: "Segmentation & Registration",
    WorkflowModule.RECONSTRUCTION.value: "MBSI Reconstruction",
    WorkflowModule.BENCHMARK.value: "Benchmark & Validation",
    WorkflowModule.DISCOVERY.value: "Discovery Intelligence",
    WorkflowModule.AI_REVIEW.value: "AI Review",
    WorkflowModule.REPORT_EXPORT.value: "Report & Export",
    WorkflowModule.SETTINGS.value: "Settings",
}

WORKFLOW_SUBSTEPS: Dict[str, List[str]] = {
    WorkflowModule.STUDY_DATA.value: [
        "project_metadata",
        "experimental_design",
        "sample_table",
        "technology_upload",
        "downloader",
        "readiness_compatibility",
    ],
    WorkflowModule.QC_TRANSFORMATION.value: [
        "original_summary",
        "filter_data",
        "normalize",
        "pseudobulk",
        "quilt_plot",
    ],
    WorkflowModule.VISUALIZATION.value: [
        "spatial_feature",
        "quilt",
        "cluster_map",
        "faceting",
        "reduction",
        "violin_dot_heatmap",
    ],
    WorkflowModule.SPATIAL_VARIABLE_GENES.value: [
        "morans_i",
        "gearys_c",
        "spatial_rank",
        "consensus_svg",
    ],
    WorkflowModule.SPATIAL_GENE_SETS.value: [
        "go_bp",
        "hallmark",
        "reactome",
        "kegg",
        "custom",
        "spatial_gsea",
    ],
    WorkflowModule.SPATIAL_DOMAINS.value: [
        "stclust",
        "leiden",
        "louvain",
        "bayesspace_graphst",
        "mbsi_graph",
    ],
    WorkflowModule.PHENOTYPING.value: [
        "marker_panels",
        "atlas_mapping",
        "tme_scoring",
        "codex_protein",
    ],
    WorkflowModule.DIFFERENTIAL_ANALYSIS.value: [
        "cluster_de",
        "domain_de",
        "region_de",
        "condition_de",
        "pseudobulk_de",
    ],
    WorkflowModule.SPATIAL_GRADIENTS.value: [
        "domain_centered",
        "tumor_margin",
        "boundary_distance",
        "ligand_diffusion",
        "custom_anchor",
    ],
    WorkflowModule.SEGMENT_REGISTER.value: [
        "tissue_segmentation",
        "cell_segmentation",
        "image_registration",
        "region_selection",
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

LEGACY_MODULE_MAP: Dict[str, str] = {
    "project_setup": WorkflowModule.STUDY_DATA.value,
    "project": WorkflowModule.STUDY_DATA.value,
    "upload": WorkflowModule.STUDY_DATA.value,
    "study_setup": WorkflowModule.STUDY_DATA.value,
    "preprocess": WorkflowModule.QC_TRANSFORMATION.value,
    "qc_preprocess": WorkflowModule.QC_TRANSFORMATION.value,
    "spatial_analysis": WorkflowModule.VISUALIZATION.value,
    "segmentation": WorkflowModule.SEGMENT_REGISTER.value,
    "communication": WorkflowModule.DISCOVERY.value,
    "tme": WorkflowModule.DISCOVERY.value,
    "ml_learning": WorkflowModule.SETTINGS.value,
    "notebook": WorkflowModule.REPORT_EXPORT.value,
    "report": WorkflowModule.REPORT_EXPORT.value,
}


def resolve_module_key(key: str) -> str:
    return LEGACY_MODULE_MAP.get(key, key)
