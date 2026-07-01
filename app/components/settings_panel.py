"""Settings panel — general, analysis, performance, platform, about."""

from __future__ import annotations

import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from app.components.page_utils import OUTPUT_DIR
from app.components.theme import THEME_KEY, get_theme, set_theme

SETTINGS_KEY = "mbsi_settings"
APP_VERSION = "0.3.0"
BUILD_DATE = "2026-07-01"


def _default_settings() -> dict:
    return {
        "language": "en",
        "autosave": True,
        "default_clustering": "leiden",
        "default_normalization": "log1p",
        "default_spatial_stats": "morans_i",
        "cpu_threads": max(1, (os.cpu_count() or 4) - 1),
        "api_endpoint": "http://127.0.0.1:8000",
        "storage_location": str(OUTPUT_DIR.resolve()),
        "logging_level": "INFO",
    }


def init_settings() -> None:
    defaults = _default_settings()
    current = st.session_state.get(SETTINGS_KEY)
    if not isinstance(current, dict):
        st.session_state[SETTINGS_KEY] = defaults
        return
    for key, val in defaults.items():
        current.setdefault(key, val)
    st.session_state[SETTINGS_KEY] = current


def get_settings() -> dict:
    init_settings()
    return st.session_state[SETTINGS_KEY]


def _git_commit_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _gpu_info() -> tuple[str, str]:
    try:
        import torch

        if torch.cuda.is_available():
            return "CUDA", torch.cuda.get_device_name(0)
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "Apple MPS", "Metal Performance Shaders"
    except Exception:
        pass
    return "CPU", "No GPU backend detected"


@st.dialog("Settings", width="large")
def _settings_dialog() -> None:
    init_settings()
    settings = get_settings()

    tab_general, tab_analysis, tab_perf, tab_platform, tab_about = st.tabs(
        ["General", "Analysis", "Performance", "Platform", "About"]
    )

    with tab_general:
        st.markdown("#### General")
        theme = get_theme()
        choice = st.radio(
            "Theme",
            options=["light", "dark"],
            format_func=lambda x: "Light" if x == "light" else "Dark",
            index=0 if theme == "light" else 1,
            key="settings_panel_theme",
            horizontal=True,
        )
        if choice != theme:
            set_theme(choice)
            st.rerun()

        settings["language"] = st.selectbox(
            "Language",
            options=["en"],
            index=0,
            key="settings_language",
        )
        settings["autosave"] = st.toggle(
            "Autosave session snapshots",
            value=bool(settings.get("autosave", True)),
            key="settings_autosave",
        )

    with tab_analysis:
        st.markdown("#### Analysis defaults")
        settings["default_clustering"] = st.selectbox(
            "Default clustering",
            ["leiden", "louvain", "bayesspace", "stclust"],
            index=["leiden", "louvain", "bayesspace", "stclust"].index(
                settings.get("default_clustering", "leiden")
            ),
            key="settings_clustering",
        )
        settings["default_normalization"] = st.selectbox(
            "Default normalization",
            ["log1p", "scran", "sctransform", "none"],
            index=["log1p", "scran", "sctransform", "none"].index(
                settings.get("default_normalization", "log1p")
            ),
            key="settings_norm",
        )
        settings["default_spatial_stats"] = st.selectbox(
            "Default spatial statistics",
            ["morans_i", "gearys_c", "spatial_rank"],
            index=["morans_i", "gearys_c", "spatial_rank"].index(
                settings.get("default_spatial_stats", "morans_i")
            ),
            key="settings_spatial_stats",
        )

    with tab_perf:
        st.markdown("#### Performance")
        backend, device = _gpu_info()
        st.metric("Compute backend", backend)
        st.caption(device)
        settings["cpu_threads"] = st.slider(
            "CPU threads",
            min_value=1,
            max_value=max(1, os.cpu_count() or 4),
            value=int(settings.get("cpu_threads", 1)),
            key="settings_cpu_threads",
        )
        if st.button("Clear Streamlit cache", key="settings_clear_cache"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("Cache cleared.")

    with tab_platform:
        st.markdown("#### Platform")
        settings["api_endpoint"] = st.text_input(
            "API endpoint",
            value=str(settings.get("api_endpoint", "http://127.0.0.1:8000")),
            key="settings_api_endpoint",
        )
        settings["storage_location"] = st.text_input(
            "Storage location",
            value=str(settings.get("storage_location", str(OUTPUT_DIR.resolve()))),
            key="settings_storage",
        )
        settings["logging_level"] = st.selectbox(
            "Logging level",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(
                str(settings.get("logging_level", "INFO")).upper()
            ),
            key="settings_log_level",
        )

    with tab_about:
        st.markdown("#### About MBSI Studio")
        st.markdown(f"**Version:** {APP_VERSION}")
        st.markdown(f"**Build date:** {BUILD_DATE}")
        st.markdown(f"**Git commit:** `{_git_commit_sha()}`")
        st.markdown(f"**Python:** {platform.python_version()} · **OS:** {platform.system()}")
        st.caption(f"Session theme key: `{THEME_KEY}` · Updated {datetime.now(timezone.utc).date().isoformat()}")

    st.session_state[SETTINGS_KEY] = settings


def render_settings_panel() -> None:
    """Header Settings button."""
    if st.button("Settings", key="header_settings_btn", help="Application settings"):
        _settings_dialog()
