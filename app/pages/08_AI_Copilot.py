import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from app.components.layout import inject_styles
from app.components.page_utils import init_session, guardrail_banner, ensure_advanced_demo, causal_warning
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.copilot import (
    answer_tissue_query,
    QUERY_TEMPLATES,
    ALLOWED_SOURCES,
    build_analysis_context,
    generate_biological_summary,
)

st.set_page_config(page_title="AI Copilot | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
guardrail_banner()
ensure_advanced_demo(show_info=False)
causal_warning()

render_topnav(active="AI Copilot")

st.markdown("### AI Tissue Copilot")
st.caption("Answers grounded in computed MBSI outputs only.")
st.caption(f"Allowed sources: {', '.join(ALLOWED_SOURCES)}")

state = build_analysis_context(dict(st.session_state))
if not state:
    state = st.session_state.analysis_state or {"metrics": st.session_state.metrics}

for t in QUERY_TEMPLATES:
    if st.button(t, key=f"tpl_{t}"):
        st.session_state.copilot_answer = answer_tissue_query(t, state)

query = st.text_input("Ask about your tissue analysis")
if st.button("Submit", type="primary") and query:
    ctx = build_analysis_context(dict(st.session_state))
    ctx["boundaries"] = st.session_state.boundaries_result
    st.session_state.copilot_answer = answer_tissue_query(query, ctx)

if "copilot_answer" in st.session_state:
    st.markdown(
        f'<div class="mbsi-panel mbsi-accent-purple">{st.session_state.copilot_answer}</div>',
        unsafe_allow_html=True,
    )

if st.button("Generate biological summary"):
    summary = generate_biological_summary(state)
    st.markdown(f'<div class="mbsi-panel">{summary}</div>', unsafe_allow_html=True)

render_statusbar(show_actions=False)
