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


DISCOVERY_NAV = [
    ("Benchmark", "pages/10_Benchmark_Hub.py"),
    ("Comms", "pages/11_Communication_Intelligence.py"),
    ("TME", "pages/12_TME_Intelligence.py"),
    ("Discovery", "pages/14_Discovery_Engine.py"),
]


def render_navbar(active: str = "Analysis") -> None:
    nav_items = [
        "Dashboard", "Upload & Data", "Preprocess", "Segmentation",
        "Run MBSI", "Analysis", "Validation", "AI Copilot", "Export",
        "Benchmark", "Comms", "TME", "Discovery",
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
    cols = st.columns(len(DISCOVERY_NAV))
    for col, (label, page_path) in zip(cols, DISCOVERY_NAV):
        with col:
            btn_type = "primary" if label == active else "secondary"
            if st.button(label, key=f"layout_nav_{label}", use_container_width=True, type=btn_type):
                st.switch_page(page_path)


def render_subtabs(active: str = "Spatial Map") -> None:
    """Static visual subtabs retained for backward compatibility."""
    tabs = ["Spatial Map", "Cell Types", "Clusters", "Neighborhoods", "Boundaries", "Pathways", "3D View"]
    html = "".join(
        f'<span class="mbsi-subtab{" active" if t == active else ""}">{t}</span>' for t in tabs
    )
    st.markdown(f'<div class="mbsi-subtabs">{html}</div>', unsafe_allow_html=True)


def render_analysis_subtabs() -> str:
    """Clickable Analysis subtab selector.

    Returns the active Analysis subtab while keeping all subtabs visible on the
    same dashboard page. This function is intentionally kept in layout.py so
    app/streamlit_app.py can import it safely.
    """
    tabs = ["Spatial Map", "Cell Types", "Clusters", "Neighborhoods", "Boundaries", "Pathways", "3D View"]

    if "analysis_subtab" not in st.session_state:
        st.session_state.analysis_subtab = "Spatial Map"

    # Compact CSS-friendly button row. Use columns so Streamlit can track clicks.
    cols = st.columns([1.0, 0.9, 0.8, 1.2, 1.0, 0.9, 0.8], gap="small")
    for col, tab in zip(cols, tabs):
        with col:
            active = st.session_state.analysis_subtab == tab
            label = f"● {tab}" if active else tab
            if st.button(
                label,
                key=f"analysis_tab_{tab}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.analysis_subtab = tab
                st.rerun()

    return st.session_state.analysis_subtab


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


__all__ = [
    "inject_styles",
    "render_navbar",
    "render_subtabs",
    "render_analysis_subtabs",
    "render_left_sidebar",
    "render_statusbar",
]
