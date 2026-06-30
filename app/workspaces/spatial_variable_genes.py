"""Spatial Variable Genes workspace."""

from __future__ import annotations

import streamlit as st

from app.workspaces._helpers import safe_register_table
from app.workspaces._spatial_page import render_continue, require_adata
from mbsi.discovery.spatial_workflow_evidence import svg_to_evidence
from mbsi.spatial_stats import spatial_autocorrelation_table


def _merge_session_findings(store) -> None:
    session = store.to_session_dict()
    st.session_state.setdefault("findings", []).extend(session.get("findings", []))
    st.session_state.setdefault("evidence", []).extend(session.get("evidence", []))


def render() -> None:
    st.markdown("### Spatial Variable Genes")
    if not require_adata("spatial_variable_genes"):
        return

    adata = st.session_state.adata
    n_top = st.slider("Top genes to test", 100, 3000, 500, key="svg_n_top")
    k = st.slider("kNN neighbors", 4, 20, 6, key="svg_k")

    if st.button("Run SVG analysis", type="primary", key="svg_run"):
        table = spatial_autocorrelation_table(adata, n_top=n_top, k=k)
        st.session_state.spatial_stats = table
        st.session_state.run_outputs["spatial_variable_genes"] = {"svg_table": table.to_dict()}
        safe_register_table("spatial_variable_genes", "svg_rankings", table)
        readiness = st.session_state.get("mbsi_readiness")
        store, warnings = svg_to_evidence(table, readiness=readiness, run_id=st.session_state.get("last_run", ""))
        _merge_session_findings(store)
        for w in warnings:
            st.warning(w)
        st.success(f"Computed SVG for {len(table)} genes.")

    if st.session_state.get("spatial_stats") is not None:
        st.dataframe(st.session_state.spatial_stats.head(30), use_container_width=True)

    render_continue("spatial_variable_genes")
