"""TME workspace."""

import streamlit as st
from app.components.interactive_figures import render_interactive_plot
from app.workspaces._helpers import add_finding, demo_banner, safe_register_finding, safe_register_table


def _run_tme() -> None:
    try:
        from mbsi.tme import make_tme_demo_adata, run_tme_analysis
        out = run_tme_analysis(make_tme_demo_adata(seed=42))
        st.session_state.tme_results = out
        st.session_state.last_run = "TME"
        summary = out.get("summary")
        n = len(summary) if summary is not None else 0
        add_finding("TME", f"{n} niche types", module="tme")
        safe_register_finding(f"Detected {n} TME niche types", section="tme", module="tme", title="TME niches")
    except Exception as exc:
        st.warning(f"TME failed: {exc}")


def render():
    demo_banner()
    action = st.session_state.pop("ribbon_action", None)
    if action == "run_tme":
        _run_tme()
    elif action == "export_tme":
        st.toast("TME report queued for export.")

    st.markdown("### TME Intelligence")
    if st.button("Run TME Analysis", type="primary", key="ws_run_tme"):
        _run_tme()

    results = st.session_state.get("tme_results")
    if not results:
        st.info("Run TME analysis to detect niches.")
        return
    summary = results.get("summary")
    if summary is not None and not summary.empty:
        safe_register_table("tme", "niche_summary", summary)
        from mbsi.visualization.tme_plots import plot_niche_summary
        render_interactive_plot(plot_niche_summary(summary), title="TME Niches", module="tme", key="tme_niches")
