"""ML Learning workspace."""

import streamlit as st
from app.workspaces._helpers import demo_banner, add_finding
from mbsi.ml_learning.recommender import recommend_next_analysis, record_user_feedback
from mbsi.ml_learning.run_store import log_analysis_run


DISCLAIMER = (
    "**ML Learning layer (research prototype):** Recommendations are heuristic and "
    "not validated for clinical or regulatory use. Do not use for patient decisions."
)


def render():
    demo_banner()
    st.markdown("### ML Learning")
    st.markdown(DISCLAIMER)
    if st.session_state.get("last_run"):
        log_analysis_run(
            module=st.session_state.get("active_module", "unknown"),
            run_name=st.session_state.last_run,
            metadata={"demo": True},
        )
    recs = recommend_next_analysis(st.session_state.get("active_module", "project_setup"))
    if recs:
        st.markdown("**Suggested next steps**")
        for r in recs:
            st.write(f"- {r}")
    rating = st.select_slider("Was this helpful?", options=[1, 2, 3, 4, 5], value=3)
    if st.button("Submit feedback"):
        record_user_feedback(st.session_state.get("active_module", "project_setup"), rating)
        add_finding("ML feedback", f"Recorded rating {rating}")
        st.toast("Feedback saved (local store).")
