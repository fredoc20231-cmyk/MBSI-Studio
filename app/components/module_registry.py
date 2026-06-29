"""SaaS module registry — 10 workflow modules (schema-first IA)."""

from __future__ import annotations

from typing import Any, Dict, List

MODULES: List[Dict[str, Any]] = [
    {
        "key": "study_setup",
        "label": "Study Setup & Data Ingestion",
        "icon": "📁",
        "section": "Core",
        "description": "Technology selection, study design, samples, file upload, readiness",
        "show_drawer": False,
    },
    {
        "key": "qc_preprocess",
        "label": "Data QC & Preprocessing",
        "icon": "🧹",
        "section": "Core",
        "description": "QC thresholds, normalization, batch/replicate checks, filtering",
        "show_drawer": False,
    },
    {
        "key": "segment_register",
        "label": "Segmentation & Registration",
        "icon": "🔬",
        "section": "Analysis",
        "description": "Tissue/cell segmentation and image registration",
        "show_drawer": False,
    },
    {
        "key": "spatial_analysis",
        "label": "Spatial Analysis",
        "icon": "🗺️",
        "section": "Analysis",
        "description": "PCA, clustering, markers, Moran's I, spatially variable genes",
        "show_drawer": False,
    },
    {
        "key": "reconstruction",
        "label": "MBSI Reconstruction",
        "icon": "🧩",
        "section": "Analysis",
        "description": "Physics-aware cell reconstruction",
        "show_drawer": False,
    },
    {
        "key": "benchmark",
        "label": "Benchmark & Validation",
        "icon": "📊",
        "section": "Discovery",
        "description": "Ground-truth benchmarking and validation metrics",
        "show_drawer": True,
    },
    {
        "key": "discovery",
        "label": "Discovery Intelligence",
        "icon": "🚀",
        "section": "Discovery",
        "description": "Communication, TME niches, biomarkers, causal drivers",
        "show_drawer": True,
    },
    {
        "key": "ai_review",
        "label": "AI Review & Evidence",
        "icon": "💬",
        "section": "Intelligence",
        "description": "Grounded outcome Q&A and evidence review",
        "show_drawer": False,
    },
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
        "label": "Admin / Settings",
        "icon": "⚙️",
        "section": "Export",
        "description": "Session, theme, and export defaults",
        "show_drawer": False,
    },
]

MODULE_KEYS = [m["key"] for m in MODULES]

DRAWER_MODULES = {m["key"] for m in MODULES if m.get("show_drawer")}

SECTION_ORDER = ["Core", "Analysis", "Discovery", "Intelligence", "Export"]

# Legacy redirects for session state and deep links
LEGACY_MODULE_ALIASES = {
    "project_setup": "study_setup",
    "project": "study_setup",
    "upload": "study_setup",
    "preprocess": "qc_preprocess",
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
