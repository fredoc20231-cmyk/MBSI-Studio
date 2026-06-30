"""Phenotyping workspace."""

from __future__ import annotations

import streamlit as st

from app.workspaces._helpers import safe_register_table
from app.workspaces._spatial_page import render_continue, require_adata
from mbsi.discovery.spatial_workflow_evidence import phenotype_to_evidence
from mbsi.phenotyping import map_atlas, score_marker_panel, score_tme
from mbsi.references.atlas_registry import list_atlases
from mbsi.references.marker_panels import list_panels


def _merge_session_findings(store) -> None:
    session = store.to_session_dict()
    st.session_state.setdefault("findings", []).extend(session.get("findings", []))
    st.session_state.setdefault("evidence", []).extend(session.get("evidence", []))


def render() -> None:
    st.markdown("### Phenotyping")
    if not require_adata("phenotyping"):
        return

    panel = st.selectbox("Marker panel", list_panels(), key="ph_panel")
    atlas = st.selectbox("Atlas mapping", list_atlases(), key="ph_atlas")

    if st.button("Run phenotyping", type="primary", key="ph_run"):
        adata = st.session_state.adata
        adata, panel_sum = score_marker_panel(adata, panel)
        adata, atlas_sum = map_atlas(adata, atlas)
        adata, tme_sum = score_tme(adata)
        st.session_state.adata = adata
        combined = panel_sum
        if not tme_sum.empty:
            combined = tme_sum
        st.session_state.run_outputs["phenotyping"] = {"panels": combined.to_dict()}
        safe_register_table("phenotyping", "phenotype_scores", combined)
        store, warnings = phenotype_to_evidence(combined, readiness=st.session_state.get("mbsi_readiness"))
        _merge_session_findings(store)
        for w in warnings:
            st.warning(w)
        st.dataframe(combined, use_container_width=True)

    render_continue("phenotyping")
