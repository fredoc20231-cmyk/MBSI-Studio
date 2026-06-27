"""Analysis page — redirects to main cockpit dashboard."""

import streamlit as st

st.set_page_config(page_title="Analysis | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")
st.switch_page("streamlit_app.py")
