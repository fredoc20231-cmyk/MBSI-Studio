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


def render_subtabs(active: str = "Spatial Map") -> None:
    """Static visual subtabs retained for backward compatibility."""
    tabs = ["Spatial Map", "Cell Types", "Clusters", "Neighborhoods", "Boundaries", "Pathways", "3D View"]
    html = "".join(
        f'<span class="mbsi-subtab{" active" if t == active else ""}">{t}</span>' for t in tabs
    )
    st.markdown(f'<div class="mbsi-subtabs">{html}</div>', unsafe_allow_html=True)


def render_analysis_subtabs() -> str:
    """Clickable Analysis subtab selector."""
    tabs = ["Spatial Map", "Cell Types", "Clusters", "Neighborhoods", "Boundaries", "Pathways", "3D View"]

    if "analysis_subtab" not in st.session_state:
        st.session_state.analysis_subtab = "Spatial Map"

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


def render_statusbar(show_actions: bool = True) -> None:
    """Deprecated — use app.components.statusbar.render_statusbar."""
    from app.components.statusbar import render_statusbar as _render_statusbar
    _render_statusbar(show_actions=show_actions)


__all__ = [
    "inject_styles",
    "render_subtabs",
    "render_analysis_subtabs",
    "render_left_sidebar",
    "render_statusbar",
]
