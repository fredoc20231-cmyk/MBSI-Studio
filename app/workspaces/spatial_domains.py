"""Spatial Domains workspace."""

from __future__ import annotations

import streamlit as st

from app.components.interactive_figures import render_interactive_plot
from app.workspaces._helpers import safe_register_table
from app.workspaces._spatial_page import render_continue, require_adata
from mbsi.discovery.spatial_workflow_evidence import domain_to_finding
from mbsi.domains import detect_domains
from mbsi.visualization.seurat_like import plot_spatial_feature


def _merge_session_findings(store) -> None:
    session = store.to_session_dict()
    st.session_state.setdefault("findings", []).extend(session.get("findings", []))
    st.session_state.setdefault("evidence", []).extend(session.get("evidence", []))


def render() -> None:
    st.markdown("### Spatial Domains")
    if not require_adata("spatial_domains"):
        return

    method = st.selectbox(
        "Domain method",
        ["leiden", "louvain", "stclust", "bayesspace", "graphst", "mbsi_graph"],
        key="sd_method",
    )
    resolution = st.slider("Resolution", 0.2, 2.0, 0.8, 0.1, key="sd_resolution")

    if st.button("Detect domains", type="primary", key="sd_run"):
        adata, summary, warnings = detect_domains(st.session_state.adata, method=method, resolution=resolution)
        st.session_state.adata = adata
        st.session_state.run_outputs["spatial_domains"] = {"summary": summary.to_dict(), "method": method}
        safe_register_table("spatial_domains", "domain_summary", summary)
        store, _ = domain_to_finding(summary, method, readiness=st.session_state.get("mbsi_readiness"))
        _merge_session_findings(store)
        for w in warnings:
            st.warning(w)
        st.dataframe(summary, use_container_width=True)

    if "domain" in st.session_state.adata.obs.columns:
        fig = plot_spatial_feature(st.session_state.adata, "domain")
        render_interactive_plot(fig, key="sd_map")

    render_continue("spatial_domains")
