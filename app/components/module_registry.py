"""SaaS module registry — full module catalog + 10-item primary navigation."""

from __future__ import annotations

from typing import Any, Dict, List

# Primary left-sidebar navigation (10 items per UI spec)
NAV_MODULES: List[Dict[str, Any]] = [
    {
        "key": "study_data",
        "label": "Study Setup & Data",
        "icon": "📁",
        "description": "Project setup, experimental design, sample table, technology-aware upload",
    },
    {
        "key": "qc_transformation",
        "label": "QC & Transformation",
        "icon": "🧹",
        "description": "QC summary, filtering, normalization, pseudobulk, quilt plots",
    },
    {
        "key": "segment_register",
        "label": "Segmentation & Registration",
        "icon": "🔬",
        "description": "Tissue/cell segmentation and image registration",
    },
    {
        "key": "spatial_analysis",
        "label": "Spatial Analysis",
        "icon": "🗺️",
        "description": "Spatial feature, quilt, cluster maps, UMAP/PCA, violin/dot/heatmap",
    },
    {
        "key": "reconstruction",
        "label": "Reconstruction",
        "icon": "🧩",
        "description": "Physics-aware cell reconstruction",
    },
    {
        "key": "benchmark",
        "label": "Benchmark & Validation",
        "icon": "📊",
        "description": "Ground-truth benchmarking and validation metrics",
        "show_drawer": True,
    },
    {
        "key": "discovery",
        "label": "Discovery Intelligence",
        "icon": "🚀",
        "description": "Communication, TME niches, biomarkers, causal drivers",
        "show_drawer": True,
    },
    {
        "key": "ai_review",
        "label": "AI Review & Evidence",
        "icon": "💬",
        "description": "Grounded outcome Q&A and evidence review",
    },
    {
        "key": "report_export",
        "label": "Report & Export",
        "icon": "📄",
        "description": "Notebook, HTML/PDF report, data bundle, downloads",
    },
    {
        "key": "settings",
        "label": "Settings",
        "icon": "⚙️",
        "description": "Session, theme, and export defaults",
    },
]

NAV_MODULE_KEYS = [m["key"] for m in NAV_MODULES]

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
        "label": "Reconstruction",
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
        "label": "AI Review & Evidence",
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
    for m in NAV_MODULES:
        if m["key"] == key or resolve_module(m["key"]) == key:
            return m
    return NAV_MODULES[0]


def module_show_drawer(key: str) -> bool:
    key = resolve_module(key)
    mod = get_module(key)
    if mod.get("show_drawer"):
        return True
    return key in DRAWER_MODULES


def next_module(key: str) -> str | None:
    """Return the next primary-nav module in workflow order, or None if last."""
    key = resolve_module(key)
    keys = NAV_MODULE_KEYS
    resolved = key
    if key not in keys:
        for nav_key in keys:
            if resolve_module(nav_key) == key or key.startswith(nav_key):
                resolved = nav_key
                break
        else:
            return keys[0]
    idx = keys.index(resolved)
    if idx + 1 < len(keys):
        return keys[idx + 1]
    return None


def search_nav_modules(query: str) -> List[Dict[str, Any]]:
    """Filter primary nav modules by label or description."""
    q = query.strip().lower()
    if not q:
        return list(NAV_MODULES)
    out: List[Dict[str, Any]] = []
    for mod in NAV_MODULES:
        hay = f"{mod.get('label', '')} {mod.get('description', '')}".lower()
        if q in hay:
            out.append(mod)
    return out
