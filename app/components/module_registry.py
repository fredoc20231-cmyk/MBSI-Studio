"""SaaS module registry — canonical workspace definitions."""

from __future__ import annotations

from typing import Any, Dict, List

MODULES: List[Dict[str, Any]] = [
    {"key": "project", "label": "Project", "icon": "🏠", "section": "Core", "description": "Project overview and readiness"},
    {"key": "upload", "label": "Upload", "icon": "📤", "section": "Core", "description": "Import spatial and clinical data"},
    {"key": "preprocess", "label": "Preprocess", "icon": "🧹", "section": "Core", "description": "QC and normalization"},
    {"key": "segmentation", "label": "Segmentation", "icon": "🔬", "section": "Core", "description": "Tissue and cell segmentation"},
    {"key": "reconstruction", "label": "Reconstruction", "icon": "🧩", "section": "Core", "description": "Run MBSI cell reconstruction"},
    {"key": "spatial_analysis", "label": "Spatial Analysis", "icon": "🗺️", "section": "Analysis", "description": "Clusters, markers, spatial stats"},
    {"key": "benchmark", "label": "Benchmark", "icon": "📊", "section": "Discovery", "description": "Ground-truth benchmarking"},
    {"key": "communication", "label": "Communication", "icon": "🔗", "section": "Discovery", "description": "L-R signaling intelligence"},
    {"key": "tme", "label": "TME", "icon": "🛡️", "section": "Discovery", "description": "Tumor microenvironment niches"},
    {"key": "discovery", "label": "Discovery", "icon": "🚀", "section": "Discovery", "description": "Biopharma discovery engine"},
    {"key": "ml_learning", "label": "ML Learning", "icon": "🤖", "section": "Intelligence", "description": "Run history and recommendations"},
    {"key": "ai_review", "label": "AI Review", "icon": "💬", "section": "Intelligence", "description": "Grounded outcome Q&A"},
    {"key": "report", "label": "Report", "icon": "📄", "section": "Export", "description": "Final HTML/PDF report bundle"},
    {"key": "settings", "label": "Settings", "icon": "⚙️", "section": "Export", "description": "Session and export settings"},
]

MODULE_KEYS = [m["key"] for m in MODULES]


def get_module(key: str) -> Dict[str, Any]:
    for m in MODULES:
        if m["key"] == key:
            return m
    return MODULES[0]
