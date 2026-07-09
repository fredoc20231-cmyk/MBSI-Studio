"""Verify Docker, run_api.sh, and Milestone 1 API entrypoint alignment."""

from __future__ import annotations

from pathlib import Path

import asyncio
import pytest

ROOT = Path(__file__).resolve().parent.parent


def _route_paths(app) -> set[str]:
    return {getattr(route, "path", "") for route in app.routes if hasattr(route, "path")}


def test_run_api_sh_uses_milestone_app():
    script = (ROOT / "scripts" / "run_api.sh").read_text(encoding="utf-8")
    assert "mbsi.api.app:app" in script
    assert "mbsi.api.main:app" not in script


def test_dockerfile_uses_milestone_app():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "mbsi.api.app:app" in dockerfile
    assert "mbsi.api.main:app" not in dockerfile


def test_docker_compose_uses_milestone_app():
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "mbsi.api.app:app" in compose
    assert "mbsi.api.main:app" not in compose


@pytest.mark.unit
def test_milestone_app_health_and_contract_routes():
    from mbsi.api.app import create_app

    app = create_app()
    paths = _route_paths(app)
    assert "/health" in paths
    assert "/api/health" in paths
    assert "/api/dataset/upload" in paths
    assert "/api/dataset/inspect" in paths
    assert "/api/workflow/run" in paths
    assert "/api/workflow/status" in paths

    health_routes = [r for r in app.routes if getattr(r, "path", None) == "/health"]
    assert health_routes
    payload = asyncio.run(health_routes[0].endpoint())
    assert payload["status"] == "healthy"
    assert "milestone_1_platforms" in payload


@pytest.mark.unit
def test_module_level_app_matches_factory():
    from mbsi.api import app, create_app

    assert app.title == create_app().title


@pytest.mark.unit
def test_cors_defaults_to_local_origins(monkeypatch):
    monkeypatch.delenv("MBSI_CORS_ORIGINS", raising=False)
    from mbsi.api.cors import cors_allow_origins

    origins = cors_allow_origins()
    assert "*" not in origins
    assert "http://localhost:8501" in origins


@pytest.mark.unit
def test_cors_env_override(monkeypatch):
    monkeypatch.setenv("MBSI_CORS_ORIGINS", "https://app.example.com,https://studio.example.com")
    from importlib import reload
    import mbsi.api.cors as cors_module

    reload(cors_module)
    assert cors_module.cors_allow_origins() == [
        "https://app.example.com",
        "https://studio.example.com",
    ]
