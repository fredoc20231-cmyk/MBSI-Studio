"""Shared discovery sub-analysis runners — real data first."""

import streamlit as st

from app.components.developer_mode import is_developer_mode
from app.workspaces._helpers import add_finding, safe_register_finding, safe_register_table


def _session_adata_or_none():
    adata = st.session_state.get("adata")
    if adata is not None and not st.session_state.get("using_synthetic_demo", False):
        return adata
    if is_developer_mode() and adata is not None:
        return adata
    return None


def run_communication() -> None:
    k = int(st.session_state.get("ctx_comm_k", 6))
    adata = _session_adata_or_none()
    if adata is None:
        st.warning("Communication analysis requires uploaded real data.")
        return
    try:
        from mbsi.communication import run_communication_analysis

        out = run_communication_analysis(adata, k=k)
        st.session_state.communication_results = out
        st.session_state.last_run = "Communication"
        top = out.get("top_pathway", "N/A")
        add_finding("Communication", f"Top pathway: {top}", module="discovery")
        safe_register_finding(f"Top pathway: {top}", section="discovery", module="discovery", title="Top pathway")
    except Exception as exc:
        st.warning(f"Communication failed: {exc}")


def run_tme() -> None:
    adata = _session_adata_or_none()
    if adata is None:
        st.warning("TME analysis requires uploaded real data.")
        return
    try:
        from mbsi.tme import run_tme_analysis

        out = run_tme_analysis(adata)
        st.session_state.tme_results = out
        st.session_state.last_run = "TME"
        summary = out.get("summary")
        n = len(summary) if summary is not None else 0
        add_finding("TME", f"{n} niche types", module="discovery")
        safe_register_finding(f"Detected {n} TME niche types", section="discovery", module="discovery", title="TME niches")
    except Exception as exc:
        st.warning(f"TME failed: {exc}")
