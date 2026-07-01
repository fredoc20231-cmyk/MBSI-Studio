"""Shared workspace helpers."""

from __future__ import annotations

import streamlit as st

from app.components.demo_data import generate_dashboard_demo
from app.components.page_utils import ensure_adata, OUTPUT_DIR


def ensure_demo():
    if "dashboard_demo" not in st.session_state:
        st.session_state.dashboard_demo = generate_dashboard_demo(seed=42)
    return st.session_state.dashboard_demo


def add_warning(msg: str) -> None:
    st.session_state.setdefault("saas_warnings", []).append(msg)


def add_finding(title: str, detail: str, module: str = "workspace") -> None:
    st.session_state.setdefault("saas_findings", []).append({"title": title, "detail": detail})
    safe_register_finding(f"{title}: {detail}", section="findings", module=module, title=title)


def safe_register_finding(text: str, section: str, module: str, title: str = "") -> None:
    try:
        from mbsi.reports.registry import register_finding
        register_finding(text, section, module, title=title)
    except Exception:
        pass


def safe_register_table(module: str, title: str, df, section: str = "tables") -> None:
    try:
        from mbsi.reports.registry import register_table
        register_table(module, title, df, section=section)
    except Exception:
        pass


def demo_banner():
    """Deprecated — demo labeling is scoped to Study & Data workspace only."""
    return
