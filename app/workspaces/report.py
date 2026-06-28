"""Report workspace."""

import streamlit as st
from app.components.page_utils import OUTPUT_DIR
from app.workspaces._helpers import demo_banner
from mbsi.reports.registry import get_registered_outputs
from mbsi.reports.final_report import (
    create_data_bundle,
    generate_final_html_report,
    generate_final_pdf_report,
)


def render():
    demo_banner()
    st.markdown("### Report Builder")
    reg = get_registered_outputs()
    st.caption(f"Registered: {len(reg.get('figures', []))} figures, {len(reg.get('tables', []))} tables")
    if st.button("Generate HTML Report", type="primary"):
        path = generate_final_html_report(OUTPUT_DIR)
        st.success(f"HTML report: {path}")
    if st.button("Generate PDF (fallback)"):
        path = generate_final_pdf_report(OUTPUT_DIR)
        st.info(f"PDF path: {path}")
    if st.button("Create data bundle"):
        path = create_data_bundle(OUTPUT_DIR)
        st.success(f"Bundle: {path}")
