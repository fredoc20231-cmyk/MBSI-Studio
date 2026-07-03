"""Bottom status bar for MBSI Studio cockpit."""

import platform

import streamlit as st

from app.components.developer_mode import is_developer_mode
from app.components.page_utils import check_backend_online, OUTPUT_DIR


def render_statusbar(show_actions: bool = True) -> None:
    """Render backend/engine/GPU/memory status and action buttons."""
    backend_ok = check_backend_online()
    st.session_state.backend_online = backend_ok

    gpu_label = "CPU"
    try:
        import torch
        if torch.cuda.is_available():
            gpu_label = torch.cuda.get_device_name(0)[:24]
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            gpu_label = "Apple MPS"
    except Exception:
        pass

    mem_mb = "—"
    try:
        import psutil
        mem_mb = f"{psutil.Process().memory_info().rss / 1e6:.0f} MB"
    except Exception:
        mem_mb = platform.system()

    last_run = st.session_state.get("last_run") or "None"
    dot = "online" if backend_ok else "offline"
    mode_label = "developer" if is_developer_mode() else "production"

    st.markdown(
        f"""
        <div class="mbsi-statusbar">
            <span><span class="mbsi-status-dot {dot}"></span>Backend: {"online" if backend_ok else "local mode"}</span>
            <span>Engine: MBSI v0.2</span>
            <span>GPU: {gpu_label}</span>
            <span>Memory: {mem_mb}</span>
            <span>Mode: {mode_label}</span>
            <span>Last run: {last_run}</span>
            <span>Output: {OUTPUT_DIR}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if show_actions:
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            if st.button("Refresh Status", key="sb_refresh"):
                st.rerun()
        with a2:
            if st.button("Save Snapshot", key="sb_save"):
                from app.components.export_buttons import save_snapshot
                path = save_snapshot()
                st.toast(f"Saved {path.name}")
        with a3:
            if st.button("Open Export", key="sb_export"):
                st.switch_page("pages/09_Export.py")
        with a4:
            if st.button("Analysis Cockpit", key="sb_analysis"):
                st.switch_page("pages/06_Analysis.py")
