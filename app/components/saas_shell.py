"""SaaS shell layout: organized left panels, top controls, workspace, results drawer."""

from __future__ import annotations

import importlib

import streamlit as st

from app.components.context_controls import render_context_controls
from app.components.header_status import (
    get_dataset_status,
    get_project_label,
    get_run_status,
    get_technology_label,
)
from app.components.help_panel import render_help_drawer
from app.components.module_registry import (
    LEGACY_MODULE_ALIASES,
    NAV_MODULES,
    get_module,
    module_show_drawer,
    resolve_module,
    search_nav_modules,
)
from app.components.notification_center import render_notification_center
from app.components.notification_center import init_notifications
from app.components.page_utils import init_session
from app.workspaces._study_setup_core import ensure_study_setup_defaults
from app.components.results_drawer import render_right_results_drawer
from app.components.settings_panel import init_settings, render_settings_panel
from app.components.statusbar import render_statusbar
from app.components.theme import inject_theme_styles, init_theme_state
from app.components.user_menu import render_user_menu


WORKSPACE_ROUTES = {
    "study_data": "app.workspaces.study_data",
    "qc_transformation": "app.workspaces.qc_transformation",
    "visualization": "app.workspaces.visualization",
    "spatial_variable_genes": "app.workspaces.spatial_variable_genes",
    "spatial_gene_sets": "app.workspaces.spatial_gene_sets",
    "spatial_domains": "app.workspaces.spatial_domains",
    "phenotyping": "app.workspaces.phenotyping",
    "differential_analysis": "app.workspaces.differential_analysis",
    "spatial_gradients": "app.workspaces.spatial_gradients",
    "segment_register": "app.workspaces.segment_register",
    "reconstruction": "app.workspaces.reconstruction",
    "benchmark": "app.workspaces.benchmark",
    "discovery": "app.workspaces.discovery",
    "ai_review": "app.workspaces.ai_review",
    "report_export": "app.workspaces.report_export",
    "settings": "app.workspaces.settings",
}

for _legacy, _canonical in LEGACY_MODULE_ALIASES.items():
    WORKSPACE_ROUTES[_legacy] = WORKSPACE_ROUTES[_canonical]


@st.dialog("Search modules", width="large")
def _search_dialog() -> None:
    query = st.text_input("Search modules", placeholder="Type to filter…", key="header_search_query")
    matches = search_nav_modules(query)
    if not matches:
        st.info("No modules match your search.")
        return
    for mod in matches:
        icon = mod.get("icon", "")
        label = mod["label"]
        btn_label = f"{icon}  {label}" if icon else label
        if st.button(btn_label, key=f"search_nav_{mod['key']}", use_container_width=True):
            st.session_state.active_module = mod["key"]
            st.rerun()


def render_module_search() -> None:
    """Header search — opens filterable module list."""
    if st.button("Search", key="header_search_btn", help="Search modules (Ctrl/Cmd+K)"):
        _search_dialog()


def init_saas_state() -> None:
    """Initialize session keys used by the SaaS shell."""
    init_session()
    ensure_study_setup_defaults()
    init_theme_state()
    init_settings()
    init_notifications()
    active = st.session_state.get("active_module", "study_data")
    st.session_state["active_module"] = resolve_module(active)
    st.session_state.setdefault("active_module", "study_data")
    st.session_state.setdefault("selected_technology", "visium")
    st.session_state.setdefault("saas_warnings", [])
    st.session_state.setdefault("saas_findings", [])
    st.session_state.setdefault("run_outputs", {})
    st.session_state.setdefault("figure_registry", {})
    st.session_state.setdefault("table_registry", {})


def _header_chip(label: str, value: str, css_class: str = "") -> str:
    cls = f"saas-header-chip-value {css_class}".strip()
    return (
        f'<div class="saas-header-chip">'
        f'<span class="saas-header-chip-label">{label}</span>'
        f'<span class="{cls}">{value}</span>'
        f"</div>"
    )


def render_product_header() -> None:
    """Compact production header: brand, context chips, action controls."""
    project = get_project_label()
    technology = get_technology_label()
    dataset_label, dataset_cls = get_dataset_status()
    run_label, run_cls = get_run_status()

    st.markdown('<span class="saas-header-anchor saas-shell-anchor"></span>', unsafe_allow_html=True)

    brand_col, meta_col, actions_col = st.columns([1.6, 4.2, 2.2], gap="small")
    with brand_col:
        st.markdown(
            """
            <div class="saas-product-header saas-header-brand">
              <div class="saas-product-brand">
                <div class="saas-logo-mark">M</div>
                <div class="saas-product-title">MBSI Studio</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with meta_col:
        chips = "".join(
            [
                _header_chip("Project", project),
                _header_chip("Technology", technology),
                _header_chip("Dataset", dataset_label, dataset_cls),
                _header_chip("Run", run_label, run_cls),
            ]
        )
        st.markdown(f'<div class="saas-header-meta">{chips}</div>', unsafe_allow_html=True)
    with actions_col:
        st.markdown('<div class="saas-header-actions-anchor"></div>', unsafe_allow_html=True)
        a1, a2, a3, a4, a5 = st.columns(5, gap="small")
        with a1:
            render_module_search()
        with a2:
            render_notification_center()
        with a3:
            render_help_drawer()
        with a4:
            render_settings_panel()
        with a5:
            render_user_menu()


def render_project_panel() -> None:
    """Static project card — buttons render as sibling Streamlit widgets below."""
    project_name = get_project_label()
    data_status, _ = get_dataset_status()
    st.markdown(
        f"""
        <div class="saas-side-card mbsi-card">
          <div class="saas-side-title">Quick actions</div>
          <div class="saas-project-name">{project_name}</div>
          <div class="saas-mini-grid">
            <div><span>Dataset</span><strong>{data_status}</strong></div>
            <div><span>Mode</span><strong>Guided</strong></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Run next step", key="saas_run_next", type="primary", use_container_width=True):
        from app.components.module_registry import next_module

        nxt = next_module(st.session_state.get("active_module", "study_data"))
        if nxt:
            st.session_state.active_module = nxt
            st.rerun()
    if st.button("Generate report", key="saas_go_report", use_container_width=True):
        st.session_state.active_module = "report_export"
        st.rerun()


def render_left_main_nav() -> None:
    """Primary workflow navigation — 10 modules per UI spec."""
    render_project_panel()
    active_key = resolve_module(st.session_state.get("active_module", "study_data"))

    st.markdown('<div class="saas-nav-list">', unsafe_allow_html=True)
    for mod in NAV_MODULES:
        key = mod["key"]
        resolved = resolve_module(key)
        active = active_key == key or active_key == resolved
        btn_type = "primary" if active else "secondary"
        icon = mod.get("icon", "")
        label = mod["label"]
        btn_label = f"{icon}  {label}" if icon else label
        if st.button(btn_label, key=f"saas_nav_{key}", type=btn_type, use_container_width=True):
            st.session_state.active_module = key
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_top_context_bar() -> None:
    """Ribbon controls — styled via .saas-top-bar-anchor on parent row."""
    active_key = resolve_module(st.session_state.get("active_module", "study_data"))
    mod = get_module(active_key)
    st.markdown('<span class="saas-top-bar-anchor saas-shell-anchor"></span>', unsafe_allow_html=True)
    title_col, control_col = st.columns([1.2, 4.8], gap="small")
    with title_col:
        icon = mod.get("icon", "")
        st.markdown(
            f"""
            <div class="saas-module-header">
              <div class="saas-module-title">{icon} {mod['label']}</div>
              <div class="saas-module-description">{mod.get('description', '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with control_col:
        render_context_controls(active_key)


def render_main_workspace() -> None:
    """Route selected module — styled via .saas-workspace-anchor on parent column."""
    key = resolve_module(st.session_state.get("active_module", "study_data"))
    mod_path = WORKSPACE_ROUTES.get(key, WORKSPACE_ROUTES["study_data"])
    full_width = not module_show_drawer(key)
    anchor_cls = "saas-workspace-anchor saas-shell-anchor"
    if full_width:
        anchor_cls += " saas-workspace-full-anchor"
    st.markdown(f'<span class="{anchor_cls}"></span>', unsafe_allow_html=True)
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


def render_saas_app() -> None:
    init_saas_state()
    inject_theme_styles()
    st.markdown('<div class="saas-app">', unsafe_allow_html=True)
    render_product_header()

    left_col, content_col = st.columns([1.15, 5.85], gap="small")
    with left_col:
        st.markdown('<span class="saas-left-nav-anchor saas-shell-anchor"></span>', unsafe_allow_html=True)
        render_left_main_nav()

    with content_col:
        render_top_context_bar()
        active_key = resolve_module(st.session_state.get("active_module", "study_data"))
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
