"""Settings workspace."""

import streamlit as st
from app.workspaces._helpers import demo_banner


def render():
    demo_banner()
    st.markdown("### Settings")
    st.toggle("Show results drawer", value=st.session_state.get("saas_drawer_open", True), key="saas_drawer_open")
    st.toggle("Demo mode banner", value=True, disabled=True)
    st.caption("Legacy multipage routes remain under app/pages/ for compatibility.")
