"""
Safe Streamlit entry — catches import errors per workspace and optional deps.
Set MBSI_SAFE_UI=1 or use scripts/start_ui.sh with SAFE=1.
"""

import importlib
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.module_registry import LEGACY_MODULE_ALIASES, MODULES, resolve_module
from app.components.page_utils import init_session
from app.components.theme import init_theme_state

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

_STARTUP_ERRORS: list[str] = []


def _safe_import(module_path: str) -> object | None:
    try:
        return importlib.import_module(module_path)
    except Exception as exc:
        _STARTUP_ERRORS.append(f"{module_path}: {exc}")
        return None


def _preflight_workspaces() -> dict[str, str | None]:
    status: dict[str, str | None] = {}
    for key, mod_path in WORKSPACE_ROUTES.items():
        try:
            importlib.import_module(mod_path)
            status[key] = None
        except Exception as exc:
            status[key] = str(exc)
    return status


def _render_safe_workspace(key: str) -> None:
    mod_path = WORKSPACE_ROUTES.get(key, WORKSPACE_ROUTES["study_data"])
    try:
        ws = importlib.import_module(mod_path)
        if hasattr(ws, "render"):
            ws.render()
        else:
            st.info(f"Workspace `{mod_path}` has no render() function yet.")
    except Exception as exc:
        st.error(f"Could not load workspace: {key}")
        st.caption(str(exc))
        with st.expander("Traceback"):
            st.code(traceback.format_exc())
        st.session_state.setdefault("saas_warnings", []).append(f"Workspace {key} failed: {exc}")


def render_safe_app() -> None:
    init_session()
    init_theme_state()
    inject_styles()

    st.markdown("## MBSI Studio (safe mode)")
    if _STARTUP_ERRORS:
        with st.expander("Startup import warnings", expanded=False):
            for msg in _STARTUP_ERRORS:
                st.warning(msg)

    ws_status = _preflight_workspaces()
    broken = {k: v for k, v in ws_status.items() if v}
    if broken:
        with st.expander("Workspace import status"):
            for k, err in sorted(broken.items()):
                st.markdown(f"**{k}**: `{err}`")

    active = resolve_module(st.session_state.get("active_module", "study_data"))
    labels = {m["key"]: f"{m.get('icon', '')} {m['label']}".strip() for m in MODULES}
    choice = st.selectbox(
        "Module",
        options=list(WORKSPACE_ROUTES.keys()),
        index=list(WORKSPACE_ROUTES.keys()).index(active) if active in WORKSPACE_ROUTES else 0,
        format_func=lambda k: labels.get(k, k),
    )
    st.session_state["active_module"] = choice
    _render_safe_workspace(choice)


st.set_page_config(
    page_title="MBSI Studio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Preflight optional deps without crashing
for _opt in (
    "cellpose",
    "gseapy",
    "squidpy",
    "tangram",
):
    _safe_import(_opt)

try:
    from app.components.saas_shell import render_saas_app

    init_theme_state()
    inject_styles()
    render_saas_app()
except Exception as shell_exc:
    st.warning(f"SaaS shell unavailable ({shell_exc}); using safe workspace router.")
    render_safe_app()
