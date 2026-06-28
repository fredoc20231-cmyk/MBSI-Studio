"""SaaS shell layout: left nav, top bar, workspace, results drawer."""

from __future__ import annotations

import streamlit as st

from app.components.context_controls import render_context_controls
from app.components.module_registry import MODULES, get_module
from app.components.page_utils import init_session
from app.components.results_drawer import render_right_results_drawer
from app.components.theme import init_theme_state, inject_theme_styles, render_theme_quick_toggle


def init_saas_state() -> None:
    init_session()
    init_theme_state()
    st.session_state.setdefault("active_module", "project")
    st.session_state.setdefault("saas_drawer_open", True)
    st.session_state.setdefault("saas_warnings", [])
    st.session_state.setdefault("saas_findings", [])


def render_left_main_nav() -> None:
    st.markdown('<div class="saas-left-nav">', unsafe_allow_html=True)
    for mod in MODULES:
        key = mod["key"]
        label = mod["label"]
        icon = mod.get("icon", "")
        active = st.session_state.get("active_module") == key
        btn_type = "primary" if active else "secondary"
        if st.button(f"{icon} {label}".strip(), key=f"nav_{key}", type=btn_type, use_container_width=True):
            st.session_state.active_module = key
            st.rerun()
    st.markdown('<div class="saas-nav-footer">', unsafe_allow_html=True)
    render_theme_quick_toggle(compact=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_top_context_bar() -> None:
    mod = get_module(st.session_state.get("active_module", "project"))
    st.markdown('<div class="saas-top-bar">', unsafe_allow_html=True)
    cols = st.columns([3, 2])
    with cols[0]:
        st.markdown(f"### {mod.get('icon', '')} {mod['label']}".strip())
        st.caption(mod.get("description", ""))
    with cols[1]:
        render_context_controls(st.session_state.get("active_module", "project"))
    st.markdown("</div>", unsafe_allow_html=True)


def render_main_workspace() -> None:
    key = st.session_state.get("active_module", "project")
    routes = {
        "project": "app.workspaces.project",
        "upload": "app.workspaces.upload",
        "preprocess": "app.workspaces.preprocess",
        "segmentation": "app.workspaces.segmentation",
        "reconstruction": "app.workspaces.reconstruction",
        "spatial_analysis": "app.workspaces.spatial_analysis",
        "benchmark": "app.workspaces.benchmark",
        "communication": "app.workspaces.communication",
        "tme": "app.workspaces.tme",
        "discovery": "app.workspaces.discovery",
        "ml_learning": "app.workspaces.ml_learning",
        "ai_review": "app.workspaces.ai_review",
        "report": "app.workspaces.report",
        "settings": "app.workspaces.settings",
    }
    mod_path = routes.get(key, routes["project"])
    import importlib

    ws = importlib.import_module(mod_path)
    st.markdown('<div class="saas-workspace">', unsafe_allow_html=True)
    ws.render()
    st.markdown("</div>", unsafe_allow_html=True)


def render_saas_app() -> None:
    init_saas_state()
    inject_theme_styles()
    st.markdown('<div class="saas-app">', unsafe_allow_html=True)
    left, main = st.columns([1, 4])
    with left:
        render_left_main_nav()
    with main:
        render_top_context_bar()
        body_cols = st.columns([3, 1] if st.session_state.get("saas_drawer_open", True) else [1])
        with body_cols[0]:
            render_main_workspace()
        if st.session_state.get("saas_drawer_open", True) and len(body_cols) > 1:
            with body_cols[1]:
                render_right_results_drawer()
    st.markdown("</div>", unsafe_allow_html=True)
