"""Deployment smoke checks for the Render-hosted FastAPI/Lovable contract."""
import pytest
from fastapi.testclient import TestClient
from mbsi.api.app import create_app
from mbsi.api.cors import cors_allow_origins


@pytest.mark.unit
def test_public_health_and_root_links():
    client = TestClient(create_app())
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["health"] == "/api/health"
    assert root.json()["openapi"] == "/openapi.json"
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert client.get("/openapi.json").status_code == 200


@pytest.mark.unit
def test_lovable_production_origin_allowed_without_env(monkeypatch):
    monkeypatch.delenv("MBSI_CORS_ORIGINS", raising=False)
    assert "https://mbsi-studio.cronus.life" in cors_allow_origins()
    client = TestClient(create_app())
    response = client.get("/api/health", headers={"Origin": "https://mbsi-studio.cronus.life"})
    assert response.headers.get("access-control-allow-origin") == "https://mbsi-studio.cronus.life"
    preflight = client.options(
        "/api/project/create",
        headers={
            "Origin": "https://mbsi-studio.cronus.life",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == "https://mbsi-studio.cronus.life"


@pytest.mark.unit
def test_cors_env_trailing_slash_is_normalized(monkeypatch):
    monkeypatch.setenv("MBSI_CORS_ORIGINS", "https://mbsi-studio.cronus.life/")
    assert cors_allow_origins() == ["https://mbsi-studio.cronus.life"]


@pytest.mark.unit
def test_observed_dataset_endpoint_is_registered():
    client = TestClient(create_app())
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    assert isinstance(response.json()["datasets"], list)
