"""SaaS shell layout: organized left panels, top controls, workspace, results drawer."""

from __future__ import annotations

import importlib
from collections import defaultdict

import streamlit as st

from app.components.context_controls import render_context_controls
from app.components.module_registry import MODULES, SECTION_ORDER, get_module, module_show_drawer
from app.components.page_utils import init_session
from app.components.results_drawer import render_right_results_drawer
from app.components.statusbar import render_statusbar
from app.components.theme import init_theme_state, inject_theme_styles, render_theme_quick_toggle


WORKSPACE_ROUTES = {
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
    "notebook": "app.workspaces.notebook",
    "report": "app.workspaces.report",
    "settings": "app.workspaces.settings",
}


def init_saas_state() -> None:
    """Initialize session keys used by the SaaS shell."""
    init_session()
    init_theme_state()
    st.session_state.setdefault("active_module", "project")
    st.session_state.setdefault("saas_warnings", [])
    st.session_state.setdefault("saas_findings", [])
    st.session_state.setdefault("run_outputs", {})
    st.session_state.setdefault("figure_registry", {})
    st.session_state.setdefault("table_registry", {})


def render_product_header() -> None:
    st.markdown(
        """
        <div class="saas-product-header">
          <div class="saas-product-brand">
            <div class="saas-logo-mark">M</div>
            <div>
              <div class="saas-product-title">MBSI Studio</div>
              <div class="saas-product-subtitle">Physics-Aware Spatial Biology Intelligence</div>
            </div>
          </div>
          <div class="saas-product-meta">
            <span class="saas-pill saas-pill-green">Demo Mode</span>
            <span class="saas-pill">Research Use</span>
            <span class="saas-pill">v2.0</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_project_panel() -> None:
    st.markdown('<div class="saas-side-card">', unsafe_allow_html=True)
    st.markdown('<div class="saas-side-title">Project</div>', unsafe_allow_html=True)
    st.markdown('<div class="saas-project-name">Ovarian Cancer — HGSOC</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="saas-mini-grid">
          <div><span>Data</span><strong>Demo</strong></div>
          <div><span>Status</span><strong>Ready</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Run next step", key="saas_run_next", type="primary", use_container_width=True):
        st.session_state.active_module = "discovery"
        st.rerun()
    if st.button("Generate report", key="saas_go_report", use_container_width=True):
        st.session_state.active_module = "report"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_left_main_nav() -> None:
    render_project_panel()
    st.markdown('<div class="saas-left-nav">', unsafe_allow_html=True)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for mod in MODULES:
        grouped[mod.get("section", "Other")].append(mod)

    for section in SECTION_ORDER:
        mods = grouped.get(section, [])
        if not mods:
            continue
        st.markdown(f'<div class="saas-nav-section">{section}</div>', unsafe_allow_html=True)
        if section == "Intelligence":
            st.markdown(
                '<div class="saas-workflow-hint">Review outcomes → export final report</div>',
                unsafe_allow_html=True,
            )
        for mod in mods:
            key = mod["key"]
            active = st.session_state.get("active_module") == key
            btn_type = "primary" if active else "secondary"
            label = f"{mod.get('icon', '')} {mod['label']}".strip()
            if st.button(label, key=f"saas_nav_{key}", type=btn_type, use_container_width=True):
                st.session_state.active_module = key
                st.rerun()

    st.markdown('<div class="saas-nav-footer">', unsafe_allow_html=True)
    render_theme_quick_toggle(compact=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_top_context_bar() -> None:
    active_key = st.session_state.get("active_module", "project")
    mod = get_module(active_key)
    st.markdown('<div class="saas-top-bar">', unsafe_allow_html=True)
    title_col, control_col = st.columns([1.4, 4.6], gap="small")
    with title_col:
        st.markdown(
            f"""
            <div class="saas-module-title">{mod.get('icon', '')} {mod['label']}</div>
            <div class="saas-module-description">{mod.get('description', '')}</div>
            """,
            unsafe_allow_html=True,
        )
    with control_col:
        render_context_controls(active_key)
    st.markdown("</div>", unsafe_allow_html=True)


def render_main_workspace() -> None:
    key = st.session_state.get("active_module", "project")
    mod_path = WORKSPACE_ROUTES.get(key, WORKSPACE_ROUTES["project"])
    full_width = not module_show_drawer(key)
    cls = "saas-workspace saas-workspace-full" if full_width else "saas-workspace"
    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
    try:
        ws = importlib.import_module(mod_path)
        if hasattr(ws, "render"):
            ws.render()
        else:
            st.info(f"Workspace `{mod_path}` has no render() function yet.")
    except Exception as exc:
        st.error(f"Could not load workspace: {key}")
        st.caption(str(exc))
        st.session_state.setdefault("saas_warnings", []).append(f"Workspace {key} failed: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_saas_app() -> None:
    init_saas_state()
    inject_theme_styles()
    st.markdown('<div class="saas-app">', unsafe_allow_html=True)
    render_product_header()

    left_col, content_col = st.columns([1.12, 5.88], gap="small")
    with left_col:
        render_left_main_nav()

    with content_col:
        render_top_context_bar()
        active_key = st.session_state.get("active_module", "project")
        if module_show_drawer(active_key):
            main_col, right_col = st.columns([4.55, 1.45], gap="small")
            with main_col:
                render_main_workspace()
            with right_col:
                render_right_results_drawer()
        else:
            render_main_workspace()

    render_statusbar(show_actions=False)
    st.markdown("</div>", unsafe_allow_html=True)
