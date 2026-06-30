"""Shared helpers for spatialGE-style workspace pages."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from app.components.module_registry import get_module, next_module


def require_adata(module_key: str) -> bool:
    """Return True if adata is present; otherwise show real-data gate message."""
    adata = st.session_state.get("adata")
    if adata is not None:
        return True
    mod = get_module(module_key)
    st.warning(f"**{mod['label']}** requires uploaded data. Complete **Study & Data** first.")
    st.info("Upload real spatial data — demo datasets are not loaded automatically.")
    if st.button("Go to Study & Data", key=f"{module_key}_goto_study"):
        st.session_state.active_module = "study_data"
        st.rerun()
    return False


def render_continue(module_key: str, label: Optional[str] = None) -> None:
    """Render Continue button to next workflow module."""
    nxt = next_module(module_key)
    if not nxt:
        return
    nxt_mod = get_module(nxt)
    btn_label = label or f"Continue to {nxt_mod['label']}"
    if st.button(btn_label, type="primary", key=f"{module_key}_continue"):
        st.session_state.active_module = nxt
        st.rerun()
