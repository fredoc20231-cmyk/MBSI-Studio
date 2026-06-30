"""Differential Analysis workspace."""

from __future__ import annotations

import streamlit as st

from app.workspaces._helpers import safe_register_table
from app.workspaces._spatial_page import render_continue, render_page_header, require_adata
from mbsi.differential import run_de
from mbsi.discovery.spatial_workflow_evidence import de_to_evidence


def _merge_session_findings(store) -> None:
    session = store.to_session_dict()
    st.session_state.setdefault("findings", []).extend(session.get("findings", []))
    st.session_state.setdefault("evidence", []).extend(session.get("evidence", []))


def render() -> None:
    render_page_header(
        "Differential Analysis",
        "Compare expression across clusters, domains, regions, or conditions.",
        icon="📈",
    )
    if not require_adata("differential_analysis"):
        return

    mode = st.selectbox(
        "DE mode",
        ["cluster", "domain", "region", "condition", "pseudobulk"],
        key="de_mode",
    )
    test = st.selectbox("Test", ["wilcoxon", "t-test"], key="de_test")

    if st.button("Run DE", type="primary", key="de_run"):
        result = run_de(st.session_state.adata, mode=mode, test=test)
        st.session_state.de_results = result
        st.session_state.run_outputs["differential_analysis"] = {"de": result.to_dict(), "mode": mode}
        safe_register_table("differential_analysis", f"de_{mode}", result)
        store, warnings = de_to_evidence(result, mode, readiness=st.session_state.get("mbsi_readiness"))
        _merge_session_findings(store)
        for w in warnings:
            st.warning(w)
        if not result.empty:
            st.dataframe(result.head(30), use_container_width=True)
        else:
            st.info("No DE results — check group labels in adata.obs.")

    render_continue("differential_analysis")
