"""AI Review workspace."""

import streamlit as st
from app.workspaces._helpers import demo_banner
from mbsi.ai_review.reviewer import answer_outcome_question

DISCLAIMER = (
    "**AI Review (rule-based, no external LLM):** Answers are grounded in registered "
    "outputs only. Not clinical decision support — validate all findings independently."
)


def render():
    demo_banner()
    st.markdown("### AI Review")
    st.markdown(DISCLAIMER)
    if "ai_chat" not in st.session_state:
        st.session_state.ai_chat = []
    for msg in st.session_state.ai_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Ask about pipeline outcomes (e.g. top benchmark method)")
    if prompt:
        st.session_state.ai_chat.append({"role": "user", "content": prompt})
        answer = answer_outcome_question(prompt)
        st.session_state.ai_chat.append({"role": "assistant", "content": answer})
        st.rerun()
