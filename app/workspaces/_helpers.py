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


def add_finding(title: str, detail: str) -> None:
    st.session_state.setdefault("saas_findings", []).append({"title": title, "detail": detail})


def demo_banner():
    st.caption("Demo mode — computational outputs for research use only.")
