"""Top navigation bar for MBSI Studio pages."""

import streamlit as st

NAV_PAGES = [
    ("Dashboard", "pages/01_Dashboard.py"),
    ("Upload & Data", "pages/02_Upload_Data.py"),
    ("Preprocess", "pages/03_Preprocess.py"),
    ("Segmentation", "pages/04_Segmentation.py"),
    ("Run MBSI", "pages/05_Run_MBSI.py"),
    ("Analysis", "pages/06_Analysis.py"),
    ("Validation", "pages/07_Validation.py"),
    ("AI Copilot", "pages/08_AI_Copilot.py"),
    ("Export", "pages/09_Export.py"),
    ("Benchmark Hub", "pages/10_Benchmark_Hub.py"),
    ("Communication", "pages/11_Communication_Intelligence.py"),
    ("TME", "pages/12_TME_Intelligence.py"),
    ("HGSOC Showcase", "pages/13_Ovarian_Cancer_Showcase.py"),
]


def render_topnav(active: str = "Dashboard") -> None:
    """Render horizontal navigation with page switch buttons."""
    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <div>
                <span style="font-size:1.25rem;font-weight:700;color:#f4f7fb;">🧬 MBSI Studio</span>
                <span style="font-size:0.8rem;color:#9aa7b8;margin-left:10px;">Spatial Biology Intelligence Cockpit</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(len(NAV_PAGES))
    for col, (label, page_path) in zip(cols, NAV_PAGES):
        with col:
            btn_type = "primary" if label == active else "secondary"
            if st.button(label, key=f"nav_{label}", use_container_width=True, type=btn_type):
                st.switch_page(page_path)
