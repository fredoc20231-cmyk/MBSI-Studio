"""Simple module embeddings for recommendation."""

from __future__ import annotations

MODULE_ORDER = [
    "project",
    "upload",
    "preprocess",
    "reconstruction",
    "spatial_analysis",
    "benchmark",
    "communication",
    "tme",
    "discovery",
    "report",
    "ml_learning",
    "ai_review",
]

NEXT_MAP = {
    "project": ["upload", "discovery"],
    "upload": ["preprocess", "reconstruction"],
    "preprocess": ["reconstruction", "spatial_analysis"],
    "reconstruction": ["spatial_analysis", "benchmark"],
    "spatial_analysis": ["benchmark", "communication"],
    "benchmark": ["communication", "tme"],
    "communication": ["tme", "discovery"],
    "tme": ["discovery", "report"],
    "discovery": ["report", "ai_review"],
    "report": ["ai_review", "ml_learning"],
    "ml_learning": ["discovery", "benchmark"],
    "ai_review": ["report", "ml_learning"],
    "settings": ["project"],
}


def module_vector(key: str) -> int:
    try:
        return MODULE_ORDER.index(key)
    except ValueError:
        return 0
