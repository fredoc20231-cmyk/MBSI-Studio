"""Top navigation bar for MBSI Studio — single clickable navbar."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

# Paths are relative to the main entry script directory (app/) when running:
#   streamlit run app/streamlit_app.py
CORE_NAV = [
    ("Dashboard", "streamlit_app.py"),
    ("Upload & Data", "pages/02_Upload_Data.py"),
    ("Preprocess", "pages/03_Preprocess.py"),
    ("Segmentation", "pages/04_Segmentation.py"),
    ("Run MBSI", "pages/05_Run_MBSI.py"),
    ("Analysis", "streamlit_app.py"),
    ("Validation", "pages/07_Validation.py"),
    ("AI Copilot", "pages/08_AI_Copilot.py"),
    ("Export", "pages/09_Export.py"),
]

EXTENDED_NAV = [
    ("Benchmark", "pages/10_Benchmark_Hub.py"),
    ("Comms", "pages/11_Communication_Intelligence.py"),
    ("TME", "pages/12_TME_Intelligence.py"),
    ("HGSOC", "pages/13_Ovarian_Cancer_Showcase.py"),
    ("Discovery", "pages/14_Discovery_Engine.py"),
]

NAV_PAGES = CORE_NAV + EXTENDED_NAV
NAV_LABELS = [label for label, _ in NAV_PAGES]


def _slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def main_script_dir() -> Path:
    """Directory containing streamlit_app.py (Streamlit multipage root)."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()
        if ctx and ctx.main_script_path:
            return Path(ctx.main_script_path).resolve().parent
    except Exception:
        pass
    return Path(__file__).resolve().parent.parent


def resolve_page_path(relative: str) -> str:
    """Validate and return a Streamlit page path for switch_page / page_link."""
    rel = relative.replace("\\", "/")
    target = main_script_dir() / rel
    if not target.is_file():
        raise FileNotFoundError(f"Navigation target not found: {target}")
    return rel


def _navigate(label: str, relative: str) -> None:
    """Navigate via switch_page with validated path."""
    path = resolve_page_path(relative)
    st.session_state.mbsi_nav_active = label
    st.switch_page(path)


def _render_nav_link(label: str, relative: str, active: str, row: str) -> None:
    """Render one nav item using page_link (preferred) or button fallback."""
    path = resolve_page_path(relative)
    is_active = label == active
    slug = _slug(label)

    if hasattr(st, "page_link"):
        try:
            st.page_link(path, label=label, use_container_width=True)
            return
        except Exception:
            pass

    if st.button(
        label,
        key=f"nav_{row}_{slug}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
    ):
        _navigate(label, relative)


def _inject_active_nav_css(active: str) -> None:
    esc = active.replace("\\", "\\\\").replace('"', '\\"')
    st.markdown(
        f"""
        <style>
        div[data-testid="stHorizontalBlock"] a[data-testid="stPageLink-{esc}"] {{
            color: #f4f7fb !important;
            font-weight: 700 !important;
            border-bottom: 2px solid #4f7cff !important;
            border-radius: 0 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topnav(active: str | None = None) -> None:
    """Render brand header + clickable nav rows (core + discovery modules)."""
    if active is None:
        active = st.session_state.get("mbsi_nav_active", "Analysis")

    st.markdown(
        """
        <div class="mbsi-navbar">
          <div class="mbsi-brand">
            <div class="mbsi-logo">MBSI</div>
            <div>
              <div class="mbsi-brand-title">MBSI Studio</div>
              <div class="mbsi-brand-sub">Physics-Aware Spatial Biology Intelligence</div>
            </div>
          </div>
          <div class="mbsi-nav-right">
            <span class="mbsi-demo-btn">Demo Mode</span>
            <span class="mbsi-icon-btn">?</span>
            <span class="mbsi-icon-btn">⚙</span>
            <span class="mbsi-avatar">AU</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f'<div class="mbsi-nav-brand-marker mbsi-nav-active-{_slug(active)}"></div>', unsafe_allow_html=True)

    core_cols = st.columns(len(CORE_NAV))
    for col, (label, path) in zip(core_cols, CORE_NAV):
        with col:
            _render_nav_link(label, path, active, row="core")

    ext_cols = st.columns(len(EXTENDED_NAV))
    for col, (label, path) in zip(ext_cols, EXTENDED_NAV):
        with col:
            _render_nav_link(label, path, active, row="ext")

    _inject_active_nav_css(active)
