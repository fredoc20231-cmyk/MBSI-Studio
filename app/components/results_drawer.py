"""Right results drawer — warnings, findings, run outputs."""

from __future__ import annotations

import streamlit as st

from app.components.results_notebook import render_results_notebook
from app.components.safe import safe_get
from mbsi.reports.registry import get_registered_outputs


def render_results_drawer() -> None:
    st.markdown('<span class="saas-drawer-anchor saas-shell-anchor"></span>', unsafe_allow_html=True)
    st.markdown("#### Insights")

    warnings = st.session_state.get("saas_warnings", [])
    if warnings:
        st.markdown("**Warnings**")
        for w in warnings[-5:]:
            st.caption(f"⚠ {w}")

    findings = st.session_state.get("saas_findings", [])
    if findings:
        st.markdown("**Top Findings**")
        for f in findings[:5]:
            st.markdown(f"- **{f.get('title', 'Finding')}**: {f.get('detail', '')}")

    outputs = get_registered_outputs()
    n_fig = len(outputs.get("figures", []))
    n_tbl = len(outputs.get("tables", []))
    st.metric("Registered outputs", f"{n_fig} fig / {n_tbl} tbl")

    discovery = st.session_state.get("discovery_results")
    if discovery:
        st.caption(f"Discovery status: {discovery.get('status', 'unknown')}")

    bench = st.session_state.get("benchmark_results")
    if bench:
        st.caption(f"Benchmark readiness: {safe_get(bench, 'readiness_score', default='—')}")

    last = st.session_state.get("last_run") or "None"
    st.caption(f"Last run: {last}")

    st.divider()
    render_results_notebook(compact=True)


render_right_results_drawer = render_results_drawer
