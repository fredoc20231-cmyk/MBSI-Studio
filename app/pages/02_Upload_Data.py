"""
Upload & Data — universal spatial omics front door.

Supports: 10x Visium, Xenium, MERFISH/MERSCOPE, CosMx, CODEX,
          generic h5ad, CSV matrix + coordinates.

After upload the user sees:
  • Platform detection banner
  • Readiness score + capability flags
  • Compatibility matrix (available / unavailable analyses)
  • Interactive Plotly spatial preview
  • One-click launch into spatial analysis
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.page_utils import (
    init_session,
    guardrail_banner,
    load_advanced_demo_into_session,
)
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from app.components.uploaders import (
    upload_panel,
    render_readiness_panel,
)

st.set_page_config(
    page_title="Upload | MBSI Studio",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session()
inject_styles()
guardrail_banner()

render_topnav(active="Upload & Data")

st.markdown("### Upload & Data")
st.caption(
    "Upload real spatial omics data from any supported platform. "
    "MBSI auto-detects the platform and shows which analyses are available."
)

# ---------------------------------------------------------------------------
# Upload workspace
# ---------------------------------------------------------------------------
result = upload_panel()

if result.get("adata") is not None:
    st.session_state.adata = result["adata"]
    st.session_state.using_synthetic_demo = False

if result.get("image") is not None:
    st.session_state.uploaded_image = result["image"]

if result.get("segmentation") is not None:
    st.session_state.uploaded_segmentation = result["segmentation"]

if result.get("ground_truth") is not None:
    st.session_state.ground_truth = result["ground_truth"]

# ---------------------------------------------------------------------------
# Post-upload: readiness panel + spatial preview
# ---------------------------------------------------------------------------
if st.session_state.adata is not None:
    st.divider()
    st.markdown("#### Dataset Summary")
    render_readiness_panel(st.session_state.adata)

    st.divider()
    st.markdown("#### Launch Analysis")
    btn1, btn2, btn3, btn4, _ = st.columns([1.2, 1.2, 1.2, 1.2, 4])
    with btn1:
        if st.button("Run QC", type="primary", use_container_width=True):
            st.switch_page("pages/03_Preprocess.py")
    with btn2:
        if st.button("Spatial Analysis", use_container_width=True):
            st.switch_page("pages/06_Analysis.py")
    with btn3:
        if st.button("Run MBSI", use_container_width=True):
            st.switch_page("pages/05_Run_MBSI.py")
    with btn4:
        if st.button("Discovery Engine", use_container_width=True):
            st.switch_page("pages/08_AI_Copilot.py")

# ---------------------------------------------------------------------------
# Demo fallback
# ---------------------------------------------------------------------------
st.divider()
col_demo, _ = st.columns([2, 6])
with col_demo:
    if st.button("Load Advanced Demo Dataset", use_container_width=True):
        with st.spinner("Generating synthetic spatial demo …"):
            load_advanced_demo_into_session(force=True)
        st.success("Advanced demo loaded.")
        st.switch_page("streamlit_app.py")

render_statusbar(show_actions=False)
