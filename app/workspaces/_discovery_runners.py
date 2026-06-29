"""Shared discovery sub-analysis runners."""

import streamlit as st

from app.workspaces._helpers import add_finding, safe_register_finding, safe_register_table


def run_communication() -> None:
    k = int(st.session_state.get("ctx_comm_k", 6))
    try:
        from mbsi.communication import make_communication_demo_adata, run_communication_analysis

        adata = make_communication_demo_adata(seed=42)
        out = run_communication_analysis(adata, k=k)
        st.session_state.communication_results = out
        st.session_state.last_run = "Communication"
        top = out.get("top_pathway", "N/A")
        add_finding("Communication", f"Top pathway: {top}", module="discovery")
        safe_register_finding(f"Top pathway: {top}", section="discovery", module="discovery", title="Top pathway")
    except Exception as exc:
        st.warning(f"Communication failed: {exc}")


def run_tme() -> None:
    try:
        from mbsi.tme import make_tme_demo_adata, run_tme_analysis

        out = run_tme_analysis(make_tme_demo_adata(seed=42))
        st.session_state.tme_results = out
        st.session_state.last_run = "TME"
        summary = out.get("summary")
        n = len(summary) if summary is not None else 0
        add_finding("TME", f"{n} niche types", module="discovery")
        safe_register_finding(f"Detected {n} TME niche types", section="discovery", module="discovery", title="TME niches")
    except Exception as exc:
        st.warning(f"TME failed: {exc}")
