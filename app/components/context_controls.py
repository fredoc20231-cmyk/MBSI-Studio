"""Module-specific context controls for top bar."""

from __future__ import annotations

import streamlit as st

from app.components.module_registry import get_module


def render_context_controls(active_module: str) -> None:
    mod = get_module(active_module)
    st.markdown(f'<span class="saas-context-module">{mod["icon"]} {mod["label"]}</span>', unsafe_allow_html=True)

    if active_module == "benchmark":
        st.selectbox("Platform", ["xenium", "cosmx", "merfish"], key="ctx_benchmark_platform", label_visibility="collapsed")
    elif active_module == "communication":
        st.slider("k neighbors", 3, 15, 6, key="ctx_comm_k")
    elif active_module == "tme":
        st.checkbox("Demo TME", value=True, key="ctx_tme_demo")
    elif active_module == "discovery":
        st.number_input("Seed", value=42, step=1, key="ctx_discovery_seed")
    elif active_module == "ml_learning":
        st.selectbox("View", ["Recommendations", "Run History", "Feedback"], key="ctx_ml_view")
    elif active_module == "ai_review":
        st.caption("Grounded Q&A — no external LLM")
    elif active_module == "report":
        st.selectbox("Format", ["HTML", "PDF fallback", "Data bundle"], key="ctx_report_fmt")
    else:
        st.caption(mod.get("description", ""))
