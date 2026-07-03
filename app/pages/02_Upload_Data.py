import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from app.components.layout import inject_styles
from app.components.developer_mode import is_developer_mode
from app.components.page_utils import (
    init_session,
    guardrail_banner,
    ensure_adata,
    load_advanced_demo_into_session,
)
from app.components.topnav import render_topnav
from app.components.uploaders import upload_panel, data_readiness_score
from app.components.statusbar import render_statusbar

st.set_page_config(page_title="Upload | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
guardrail_banner()
ensure_adata(show_warning=False)

render_topnav(active="Upload & Data")

st.markdown("### Upload & Data")
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

if st.session_state.adata is not None:
    score, msg = data_readiness_score(st.session_state.adata)
    st.metric("Data Readiness", f"{score}/100", msg)
    coords = st.session_state.adata.obsm.get("spatial")
    if coords is not None:
        st.scatter_chart({"x": coords[:, 0], "y": coords[:, 1]})

if is_developer_mode() and st.button("Load Advanced Demo Instead"):
    load_advanced_demo_into_session(force=True)
    st.rerun()

render_statusbar(show_actions=False)
