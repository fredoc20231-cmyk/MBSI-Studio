"""Upload workspace."""

import streamlit as st
from app.components.page_utils import ensure_adata
from app.workspaces._helpers import demo_banner, add_warning


def render():
    demo_banner()
    ensure_adata(show_warning=False)
    st.markdown("### Upload & Data")
    if st.session_state.get("adata") is None:
        st.info("No data loaded — using synthetic demo when pipelines run.")
        add_warning("No uploaded AnnData in session")
    else:
        adata = st.session_state.adata
        st.success(f"Loaded: {adata.n_obs} spots × {adata.n_vars} genes")
    st.caption("Use legacy page pages/02_Upload_Data.py for full uploader UI.")
