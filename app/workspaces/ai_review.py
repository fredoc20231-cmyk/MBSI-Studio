"""AI Review workspace."""

import streamlit as st

from app.components.page_header import render_page_header
from app.workspaces._helpers import demo_banner
from mbsi.ai_review.reviewer import answer_outcome_question

DISCLAIMER = (
    "**AI Review (rule-based, no external LLM):** Answers are grounded in registered "
    "outputs only. Not clinical decision support — validate all findings independently."
)


def render():
    demo_banner()
    render_page_header(
        "AI Outcome Review",
        "Ask grounded questions about registered analysis outputs.",
        icon="🤖",
    )
    st.markdown(
        '<div class="saas-workflow-hint">Next step: open <strong>Report & Export</strong> to generate the final deliverable.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(DISCLAIMER)

    readiness = st.session_state.get("mbsi_readiness") or {}
    project = st.session_state.get("project_metadata") or {}
    target = project.get("experimental_target") or readiness.get("experimental_target", "")
    hypothesis = project.get("hypothesis") or readiness.get("hypothesis", "")
    if target or hypothesis:
        with st.expander("Study context (from Study & Data)", expanded=True):
            if target:
                st.markdown(f"**Experimental target:** {target}")
            if hypothesis:
                st.markdown(f"**Hypothesis:** {hypothesis}")
            obj = project.get("study_objective") or project.get("biological_question", "")
            if obj:
                st.markdown(f"**Objective:** {obj}")

    findings = st.session_state.get("findings") or []
    if findings:
        st.caption(f"{len(findings)} grounded findings available for Q&A")
    if "ai_chat" not in st.session_state:
        st.session_state.ai_chat = []
    for msg in st.session_state.ai_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Ask about pipeline outcomes (e.g. top SVG genes, domain count)")
    if prompt:
        st.session_state.ai_chat.append({"role": "user", "content": prompt})
        context_prefix = ""
        if hypothesis:
            context_prefix = f"[Hypothesis: {hypothesis}] "
        answer = answer_outcome_question(context_prefix + prompt)
        st.session_state.ai_chat.append({"role": "assistant", "content": answer})
        st.rerun()
    if st.button("Go to Report & Export", key="ai_to_report"):
        st.session_state.active_module = "report_export"
        st.rerun()
