"""SaaS module registry — 16-module spatialGE-style guided workflow."""

from __future__ import annotations

from typing import Any, Dict, List

MODULES: List[Dict[str, Any]] = [
    # Setup
    {
        "key": "study_data",
        "label": "Study & Data",
        "icon": "📁",
        "section": "Setup",
        "description": "Project setup, experimental design, sample table, technology-aware upload",
        "show_drawer": False,
    },
    {
        "key": "qc_transformation",
        "label": "QC & Transformation",
        "icon": "🧹",
        "section": "Setup",
        "description": "QC summary, filtering, normalization, pseudobulk, quilt plots",
        "show_drawer": False,
    },
    # Core Spatial Analysis
    {
        "key": "visualization",
        "label": "Visualization",
        "icon": "🗺️",
        "section": "Core Spatial Analysis",
        "description": "Spatial feature, quilt, cluster maps, UMAP/PCA, violin/dot/heatmap",
        "show_drawer": False,
    },
    {
        "key": "spatial_variable_genes",
        "label": "Spatial Variable Genes",
        "icon": "🧬",
        "section": "Core Spatial Analysis",
        "description": "Moran's I, Geary's C, spatial rank, consensus SVG",
        "show_drawer": False,
    },
    {
        "key": "spatial_gene_sets",
        "label": "Spatial Gene Sets",
        "icon": "📚",
        "section": "Core Spatial Analysis",
        "description": "GO, Hallmark, Reactome, KEGG, custom, spatial GSEA",
        "show_drawer": False,
    },
    {
        "key": "spatial_domains",
        "label": "Spatial Domains",
        "icon": "🧩",
        "section": "Core Spatial Analysis",
        "description": "STclust, Leiden, Louvain, BayesSpace/GraphST, MBSI graph domains",
        "show_drawer": False,
    },
    {
        "key": "phenotyping",
        "label": "Phenotyping",
        "icon": "🏷️",
        "section": "Core Spatial Analysis",
        "description": "Marker panels, atlas mapping, TME scoring, CODEX protein labels",
        "show_drawer": False,
    },
    {
        "key": "differential_analysis",
        "label": "Differential Analysis",
        "icon": "📈",
        "section": "Core Spatial Analysis",
        "description": "Cluster/domain/region/condition DE, pseudobulk, replicate-aware",
        "show_drawer": False,
    },
    {
        "key": "spatial_gradients",
        "label": "Spatial Gradients",
        "icon": "🌊",
        "section": "Core Spatial Analysis",
        "description": "Domain-centered, tumor-margin, boundary distance, ligand diffusion",
        "show_drawer": False,
    },
    # MBSI Intelligence
    {
        "key": "segment_register",
        "label": "Segmentation & Registration",
        "icon": "🔬",
        "section": "MBSI Intelligence",
        "description": "Tissue/cell segmentation and image registration",
        "show_drawer": False,
    },
    {
        "key": "reconstruction",
        "label": "MBSI Reconstruction",
        "icon": "🧩",
        "section": "MBSI Intelligence",
        "description": "Physics-aware cell reconstruction",
        "show_drawer": False,
    },
    {
        "key": "benchmark",
        "label": "Benchmark & Validation",
        "icon": "📊",
        "section": "MBSI Intelligence",
        "description": "Ground-truth benchmarking and validation metrics",
        "show_drawer": True,
    },
    {
        "key": "discovery",
        "label": "Discovery Intelligence",
        "icon": "🚀",
        "section": "MBSI Intelligence",
        "description": "Communication, TME niches, biomarkers, causal drivers",
        "show_drawer": True,
    },
    {
        "key": "ai_review",
        "label": "AI Review",
        "icon": "💬",
        "section": "MBSI Intelligence",
        "description": "Grounded outcome Q&A and evidence review",
        "show_drawer": False,
    },
    # Export
    {
        "key": "report_export",
        "label": "Report & Export",
        "icon": "📄",
        "section": "Export",
        "description": "Notebook, HTML/PDF report, data bundle, downloads",
        "show_drawer": False,
    },
    {
        "key": "settings",
        "label": "Settings",
        "icon": "⚙️",
        "section": "Export",
        "description": "Session, theme, and export defaults",
        "show_drawer": False,
    },
]

MODULE_KEYS = [m["key"] for m in MODULES]

DRAWER_MODULES = {m["key"] for m in MODULES if m.get("show_drawer")}

SECTION_ORDER = ["Setup", "Core Spatial Analysis", "MBSI Intelligence", "Export"]

# Legacy redirects for session state and deep links
LEGACY_MODULE_ALIASES = {
    "project_setup": "study_data",
    "project": "study_data",
    "upload": "study_data",
    "study_setup": "study_data",
    "preprocess": "qc_transformation",
    "qc_preprocess": "qc_transformation",
    "spatial_analysis": "visualization",
    "segmentation": "segment_register",
    "communication": "discovery",
    "tme": "discovery",
    "ml_learning": "settings",
    "notebook": "report_export",
    "report": "report_export",
}


def resolve_module(key: str) -> str:
    return LEGACY_MODULE_ALIASES.get(key, key)


def get_module(key: str) -> Dict[str, Any]:
    key = resolve_module(key)
    for m in MODULES:
        if m["key"] == key:
            return m
    return MODULES[0]


def module_show_drawer(key: str) -> bool:
    return bool(get_module(key).get("show_drawer", False))


def next_module(key: str) -> str | None:
    """Return the next module in workflow order, or None if last."""
    key = resolve_module(key)
    keys = MODULE_KEYS
    if key not in keys:
        return keys[0]
    idx = keys.index(key)
    if idx + 1 < len(keys):
        return keys[idx + 1]
    return None
