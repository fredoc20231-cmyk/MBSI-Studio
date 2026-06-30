"""Spatial Gradients workspace."""

from __future__ import annotations

import streamlit as st

from app.workspaces._helpers import safe_register_table
from app.workspaces._spatial_page import render_continue, require_adata
from mbsi.discovery.spatial_workflow_evidence import gradient_to_evidence
from mbsi.gradients import compute_gradient


def _merge_session_findings(store) -> None:
    session = store.to_session_dict()
    st.session_state.setdefault("findings", []).extend(session.get("findings", []))
    st.session_state.setdefault("evidence", []).extend(session.get("evidence", []))


def render() -> None:
    st.markdown("### Spatial Gradients")
    if not require_adata("spatial_gradients"):
        return

    mode = st.selectbox(
        "Gradient mode",
        ["domain_centered", "tumor_margin", "boundary_distance", "ligand_diffusion", "custom_anchor"],
        key="gr_mode",
    )
    anchor = st.selectbox(
        "Anchor column",
        [c for c in ("domain", "condition", "tissue_region") if c in st.session_state.adata.obs.columns] or ["domain"],
        key="gr_anchor",
    )
    gene = st.text_input("Focus gene (optional)", key="gr_gene")

    if st.button("Compute gradients", type="primary", key="gr_run"):
        table, warnings = compute_gradient(
            st.session_state.adata,
            mode=mode,
            anchor_key=anchor,
            gene=gene,
        )
        st.session_state.run_outputs["spatial_gradients"] = {"gradient": table.to_dict(), "mode": mode}
        safe_register_table("spatial_gradients", "gradient_table", table)
        store, w2 = gradient_to_evidence(table, mode, readiness=st.session_state.get("mbsi_readiness"))
        _merge_session_findings(store)
        for w in warnings + w2:
            st.warning(w)
        st.dataframe(table.head(20), use_container_width=True)

    render_continue("spatial_gradients")
