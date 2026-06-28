"""SaaS module registry — canonical workspace definitions."""

from __future__ import annotations

from typing import Any, Dict, List

MODULES: List[Dict[str, Any]] = [
    {"key": "project", "label": "Project", "icon": "🏠", "section": "Core", "description": "Project overview and readiness", "show_drawer": False},
    {"key": "upload", "label": "Upload", "icon": "📤", "section": "Core", "description": "Import spatial and clinical data", "show_drawer": False},
    {"key": "preprocess", "label": "Preprocess", "icon": "🧹", "section": "Core", "description": "QC and normalization", "show_drawer": False},
    {"key": "segmentation", "label": "Segmentation", "icon": "🔬", "section": "Core", "description": "Tissue and cell segmentation", "show_drawer": False},
    {"key": "reconstruction", "label": "Reconstruction", "icon": "🧩", "section": "Core", "description": "Run MBSI cell reconstruction", "show_drawer": False},
    {"key": "spatial_analysis", "label": "Spatial Analysis", "icon": "🗺️", "section": "Analysis", "description": "Clusters, markers, spatial stats", "show_drawer": False},
    {"key": "benchmark", "label": "Benchmark", "icon": "📊", "section": "Discovery", "description": "Ground-truth benchmarking", "show_drawer": True},
    {"key": "communication", "label": "Communication", "icon": "🔗", "section": "Discovery", "description": "L-R signaling intelligence", "show_drawer": True},
    {"key": "tme", "label": "TME", "icon": "🛡️", "section": "Discovery", "description": "Tumor microenvironment niches", "show_drawer": True},
    {"key": "discovery", "label": "Discovery", "icon": "🚀", "section": "Discovery", "description": "Biopharma discovery engine", "show_drawer": True},
    {"key": "ml_learning", "label": "ML Learning", "icon": "🤖", "section": "Intelligence", "description": "Run history and recommendations", "show_drawer": False},
    {"key": "ai_review", "label": "AI Outcome Review", "icon": "💬", "section": "Intelligence", "description": "Grounded outcome Q&A", "show_drawer": False},
    {"key": "notebook", "label": "Results Notebook", "icon": "📓", "section": "Export", "description": "Chronological figures, tables, and findings", "show_drawer": False},
    {"key": "report", "label": "Report & Export", "icon": "📄", "section": "Export", "description": "Final HTML/PDF report bundle", "show_drawer": False},
    {"key": "settings", "label": "Settings", "icon": "⚙️", "section": "Export", "description": "Session and export settings", "show_drawer": False},
]

MODULE_KEYS = [m["key"] for m in MODULES]

DRAWER_MODULES = {m["key"] for m in MODULES if m.get("show_drawer")}

SECTION_ORDER = ["Core", "Analysis", "Discovery", "Intelligence", "Export"]


def get_module(key: str) -> Dict[str, Any]:
    for m in MODULES:
        if m["key"] == key:
            return m
    return MODULES[0]


def module_show_drawer(key: str) -> bool:
    return bool(get_module(key).get("show_drawer", False))
