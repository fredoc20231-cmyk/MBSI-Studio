"""Layout helpers — CSS injection and HTML chrome."""

from pathlib import Path

import streamlit as st


def inject_styles() -> None:
    css_paths = [
        Path(__file__).parent.parent / "style.css",
        Path(__file__).parent.parent / "assets" / "style.css",
    ]
    css = ""
    for p in css_paths:
        if p.exists():
            css += p.read_text()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_navbar(active: str = "Analysis") -> None:
    nav_items = [
        "Dashboard", "Upload & Data", "Preprocess", "Segmentation",
        "Run MBSI", "Analysis", "Validation", "AI Copilot", "Export",
    ]
    nav_html = "".join(
        f'<span class="mbsi-nav-item{" active" if n == active else ""}">{n}</span>'
        for n in nav_items
    )
    st.markdown(
        f"""
        <div class="mbsi-navbar">
          <div class="mbsi-brand">
            <div class="mbsi-logo">MBSI</div>
            <div>
              <div class="mbsi-brand-title">MBSI Studio</div>
              <div class="mbsi-brand-sub">Physics-Aware Spatial Biology Intelligence</div>
            </div>
          </div>
          <div class="mbsi-nav-center">{nav_html}</div>
          <div class="mbsi-nav-right">
            <span class="mbsi-demo-btn">Demo Mode</span>
            <span class="mbsi-icon-btn">?</span>
            <span class="mbsi-icon-btn">⚙</span>
            <span class="mbsi-avatar">AU</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Compact page navigation (Streamlit page links)
    try:
        pl_cols = st.columns(9)
        pages = [
            ("Dashboard", "streamlit_app.py"),
            ("Upload", "pages/02_Upload_Data.py"),
            ("Preprocess", "pages/03_Preprocess.py"),
            ("Segmentation", "pages/04_Segmentation.py"),
            ("Run MBSI", "pages/05_Run_MBSI.py"),
            ("Analysis", "streamlit_app.py"),
            ("Validation", "pages/07_Validation.py"),
            ("Copilot", "pages/08_AI_Copilot.py"),
            ("Export", "pages/09_Export.py"),
        ]
        for col, (label, path) in zip(pl_cols, pages):
            with col:
                st.page_link(path, label=label, use_container_width=True)
    except Exception:
        pass


def render_subtabs(active: str = "Spatial Map") -> None:
    tabs = ["Spatial Map", "Cell Types", "Clusters", "Neighborhoods", "Boundaries", "Pathways", "3D View"]
    html = "".join(
        f'<span class="mbsi-subtab{" active" if t == active else ""}">{t}</span>' for t in tabs
    )
    st.markdown(f'<div class="mbsi-subtabs">{html}</div>', unsafe_allow_html=True)


def render_left_sidebar(summary: dict) -> None:
    st.markdown('<div class="mbsi-panel"><div class="mbsi-panel-title">Project & Data</div>', unsafe_allow_html=True)
    st.selectbox("Project", ["Ovarian Cancer — High Grade Serous"], label_visibility="collapsed", key="proj_sel")
    rows = [
        ("Spots", f"{summary['spots']:,}"),
        ("Genes", f"{summary['genes']:,}"),
        ("Estimated Cells", f"{summary['cells']:,}"),
        ("Tissue Area", f"{summary['tissue_area_mm2']} mm²"),
        ("Image Resolution", f"{summary['resolution_um']} µm / px"),
    ]
    for label, val in rows:
        st.markdown(f'<div class="mbsi-row"><span>{label}</span><span>{val}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="mbsi-panel-title" style="margin-top:10px;">Data Modalities</div>', unsafe_allow_html=True)
    for m in ["Spatial Transcriptomics (Visium HD)", "H&E Histology", "Nuclei Segmentation",
              "Protein (CODEX)", "Mutation (WES)", "Clinical Data"]:
        st.markdown(f'<div style="font-size:0.75rem;"><span class="mbsi-check">✓</span>{m}</div>', unsafe_allow_html=True)
    st.markdown('<div class="mbsi-panel-title" style="margin-top:10px;">Analysis Status</div>', unsafe_allow_html=True)
    for s in ["Data Loaded", "Preprocessing", "Segmentation", "MBSI Reconstruction", "Boundary Detection",
              "Communication Analysis", "Causal Modeling", "All Modules Ready"]:
        st.markdown(f'<div style="font-size:0.75rem;"><span class="mbsi-check">✓</span>{s}</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align:center;margin:10px 0;">
          <div class="mbsi-readiness-ring"><div class="mbsi-readiness-inner">98%</div></div>
          <div style="color:#39d98a;font-weight:700;font-size:0.8rem;">Excellent</div>
          <div style="color:#9aa7b8;font-size:0.68rem;">All systems ready for advanced analysis</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_statusbar() -> None:
    try:
        import psutil
        mem = psutil.virtual_memory()
        mem_str = f"{mem.used / 1e9:.1f} / {mem.total / 1e9:.1f} GB"
    except Exception:
        mem_str = "21.4 / 23.6 GB"
    st.markdown(
        f"""
        <div class="mbsi-statusbar">
          <div class="mbsi-status-left">
            <span><strong style="color:#f4f7fb;">System Status</strong></span>
            <span><span class="mbsi-status-dot"></span>Backend: Online</span>
            <span><span class="mbsi-status-dot"></span>MBSI Engine: Ready</span>
            <span><span class="mbsi-status-dot"></span>GPU: Available (RTX 4090)</span>
            <span>Memory: {mem_str}</span>
            <span>Last Run: 2 min ago</span>
          </div>
          <div class="mbsi-status-actions">
            <span style="color:#9b6cff;">AI Copilot</span>
            <span style="color:#4f7cff;margin-left:12px;">Quick Report</span>
            <span style="color:#9aa7b8;margin-left:12px;">Export All</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
