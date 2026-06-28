"""Top navigation bar for MBSI Studio — button-based navigation (reliable)."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

# Paths relative to app/ when running: streamlit run app/streamlit_app.py
APP_DIR = Path(__file__).resolve().parent.parent

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


def resolve_page_path(relative: str) -> str:
    """Validate path exists under app/ and return normalized relative path."""
    rel = relative.replace("\\", "/")
    if not (APP_DIR / rel).is_file():
        raise FileNotFoundError(f"Missing nav target: {APP_DIR / rel}")
    return rel


def _go(label: str, relative: str) -> None:
    """Navigate to page — always uses st.switch_page (proven multipage API)."""
    st.session_state.mbsi_nav_active = label
    st.switch_page(resolve_page_path(relative))


def _nav_button(label: str, relative: str, active: str, row: str) -> None:
    """Render one navbar tab as a Streamlit button."""
    slug = _slug(label)
    is_active = label == active
    if st.button(
        label,
        key=f"mbsi_nav_{row}_{slug}",
        use_container_width=True,
        type="primary" if is_active else "secondary",
    ):
        _go(label, relative)


def render_topnav(active: str | None = None) -> None:
    """Render clickable navbar — brand row + core tabs + discovery tabs."""
    if active is None:
        active = st.session_state.get("mbsi_nav_active", "Analysis")

    # Brand row (Streamlit-native, no HTML overlay on tabs)
    brand_left, brand_right = st.columns([3, 1])
    with brand_left:
        st.markdown(
            """
            <div class="mbsi-nav-brand-inline">
              <span class="mbsi-logo-inline">MBSI</span>
              <span>
                <span class="mbsi-brand-title">MBSI Studio</span>
                <span class="mbsi-brand-sub">Physics-Aware Spatial Biology Intelligence</span>
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with brand_right:
        st.markdown(
            """
            <div class="mbsi-nav-right-inline">
              <span class="mbsi-demo-btn">Demo Mode</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="mbsi-nav-row-start"></div>', unsafe_allow_html=True)

    core_cols = st.columns(len(CORE_NAV))
    for col, (label, path) in zip(core_cols, CORE_NAV):
        with col:
            _nav_button(label, path, active, row="core")

    ext_cols = st.columns(len(EXTENDED_NAV))
    for col, (label, path) in zip(ext_cols, EXTENDED_NAV):
        with col:
            _nav_button(label, path, active, row="ext")
