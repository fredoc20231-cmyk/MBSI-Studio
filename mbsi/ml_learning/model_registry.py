"""Model registry stub for ML learning layer."""

from __future__ import annotations

from typing import Any, Dict, List

_MODELS: List[Dict[str, Any]] = [
    {"name": "heuristic_recommender", "version": "0.1", "status": "active"},
]


def list_models() -> List[Dict[str, Any]]:
    return list(_MODELS)


def register_model(name: str, version: str, metadata: Dict[str, Any] | None = None) -> None:
    _MODELS.append({"name": name, "version": version, "status": "active", **(metadata or {})})
