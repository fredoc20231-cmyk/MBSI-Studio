"""Report workspace."""

import streamlit as st
from app.components.page_utils import OUTPUT_DIR
from app.workspaces._helpers import demo_banner
from mbsi.reports.final_report import create_data_bundle, generate_final_html_report, generate_final_pdf_report
from mbsi.reports.registry import get_notebook_entries, get_registered_outputs


def _generate(kind: str) -> None:
    entries = get_notebook_entries()
    if not entries:
        st.warning("Notebook is empty — run analyses first to auto-register outputs.")
    if kind == "html":
        path = generate_final_html_report(OUTPUT_DIR)
        st.success(f"HTML report: {path}")
    elif kind == "pdf":
        path = generate_final_pdf_report(OUTPUT_DIR)
        st.info(f"PDF path: {path}")
    elif kind == "bundle":
        path = create_data_bundle(OUTPUT_DIR)
        st.success(f"Bundle: {path}")


def render():
    demo_banner()
    st.markdown(
        '<span class="saas-report-final-badge">Final deliverable</span>',
        unsafe_allow_html=True,
    )
    st.markdown("### Report & Export")
    reg = get_registered_outputs()
    entries = get_notebook_entries()
    st.caption(
        f"Notebook: {len(entries)} entries — "
        f"{len(reg.get('figures', []))} figures, {len(reg.get('tables', []))} tables, "
        f"{len(reg.get('findings', []))} findings (auto-included in export)"
    )

    action = st.session_state.pop("ribbon_action", None)
    if action == "gen_html":
        _generate("html")
    elif action == "gen_pdf":
        _generate("pdf")
    elif action == "gen_bundle":
        _generate("bundle")

    if st.button("Generate HTML Report", type="primary", key="ws_gen_html"):
        _generate("html")
    if st.button("Generate PDF (fallback)", key="ws_gen_pdf"):
        _generate("pdf")
    if st.button("Create data bundle", key="ws_gen_bundle"):
        _generate("bundle")
