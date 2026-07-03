"""Tests for production vs developer mode gating."""

import os

from app.components.developer_mode import is_developer_mode, production_mode_message


def test_production_mode_default(monkeypatch):
    monkeypatch.delenv("DEVELOPER_MODE", raising=False)
    assert is_developer_mode() is False


def test_developer_mode_env(monkeypatch):
    monkeypatch.setenv("DEVELOPER_MODE", "true")
    assert is_developer_mode() is True


def test_load_demo_blocked_in_production(monkeypatch):
    monkeypatch.delenv("DEVELOPER_MODE", raising=False)
    from app.components.page_utils import load_advanced_demo_into_session

    class _State(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    import app.components.page_utils as pu

    pu.st.session_state = _State(spatial_demo=None)
    assert load_advanced_demo_into_session(force=True) is False


def test_production_message_mentions_upload():
    assert "Study & Data" in production_mode_message()
