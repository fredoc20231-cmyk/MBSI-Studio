"""Tests for production health/readiness endpoints and CORS configuration."""

import os

from fastapi.testclient import TestClient

import mbsi.api.main as main


client = TestClient(main.app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_healthz_alias():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_readyz_endpoint():
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_cors_default_is_wildcard(monkeypatch):
    monkeypatch.delenv("MBSI_CORS_ALLOW_ORIGINS", raising=False)
    assert main._cors_allow_origins() == ["*"]


def test_cors_explicit_allowlist(monkeypatch):
    monkeypatch.setenv("MBSI_CORS_ALLOW_ORIGINS", "https://a.com, https://b.com")
    assert main._cors_allow_origins() == ["https://a.com", "https://b.com"]
