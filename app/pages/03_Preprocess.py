import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from app.components.layout import inject_styles
from app.components.page_utils import init_session, guardrail_banner, ensure_adata, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar

st.set_page_config(page_title="Preprocess | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
guardrail_banner()
ensure_adata(show_warning=False)

render_topnav(active="Preprocess")

st.markdown("### Preprocessing & QC")

min_counts = st.slider("Min counts per spot", 0, 500, 100)
max_mt = st.slider("Max mitochondrial %", 0.0, 100.0, 20.0)
n_hvg = st.number_input("Highly variable genes", 500, 5000, 2000, step=100)

if st.button("Run QC", type="primary"):
    st.session_state.preprocessing_params = {
        "min_counts": min_counts,
        "max_mt_pct": max_mt,
        "n_hvg": n_hvg,
    }
    st.session_state.last_run = "Preprocessing QC"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    st.success("QC parameters saved.")

if st.session_state.preprocessing_params:
    st.json(st.session_state.preprocessing_params)

if st.session_state.adata is not None:
    import numpy as np
    totals = np.array(st.session_state.adata.X.sum(axis=1)).flatten()
    st.markdown("**Spot total counts**")
    st.bar_chart(totals[: min(50, len(totals))])

render_statusbar(show_actions=False)
