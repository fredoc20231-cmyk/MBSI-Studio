"""Upload workspace — universal spatial omics ingestion front door."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from app.components.interactive_figures import render_interactive_plot
from app.components.uploaders import data_readiness_score, upload_panel
from app.components.page_utils import load_advanced_demo_into_session
from app.workspaces._helpers import add_finding, safe_register_finding
from mbsi.visualization.analysis_plots import plot_qc_spatial


def _store_ingestion(result: dict) -> None:
    """Persist ingestion bundle in session_state."""
    adata = result.get("adata")
    if adata is not None:
        st.session_state.adata = adata
        st.session_state.using_synthetic_demo = False

    detection = result.get("detection", {})
    platform = result.get("platform", detection.get("platform", "unknown"))
    score = result.get("readiness_score", 0)
    readiness = result.get("readiness", {})
    compatibility = result.get("compatibility", {})

    st.session_state.ingestion_result = {
        "detection": detection,
        "platform": platform,
        "readiness_score": score,
        "readiness": readiness,
        "compatibility": compatibility,
        "source": result.get("source"),
    }
    st.session_state.mbsi_platform = platform
    st.session_state.mbsi_readiness = readiness

    if result.get("image") is not None:
        st.session_state.uploaded_image = result["image"]
    if result.get("segmentation") is not None:
        st.session_state.uploaded_segmentation = result["segmentation"]


def _render_detection_panel(detection: dict) -> None:
    st.markdown("**Platform detection**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Platform", detection.get("platform", "unknown"))
    c2.metric("Confidence", f"{detection.get('confidence', 0):.0%}")
    c3.metric("Files scanned", detection.get("n_files", 0))

    if detection.get("required_found"):
        st.caption(f"Found: {', '.join(detection['required_found'])}")
    if detection.get("optional_found"):
        st.caption(f"Optional: {', '.join(detection['optional_found'])}")
    if detection.get("missing"):
        st.warning(f"Missing: {', '.join(detection['missing'])}")


def _render_compatibility_panel(compatibility: dict) -> None:
    st.markdown("**Module compatibility**")
    rows = []
    for module, info in sorted(compatibility.items()):
        rows.append({
            "Module": module.replace("_", " ").title(),
            "Status": info.get("status", "unknown"),
            "Reason": info.get("reason", ""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_spatial_preview(adata) -> None:
    st.markdown("**Spatial preview**")
    color_by = "total_counts"
    if "cell_type" in adata.obs.columns:
        color_by = "cell_type"
    elif "cluster" in adata.obs.columns:
        color_by = "cluster"
    elif "total_counts" not in adata.obs.columns:
        color_by = None

    if color_by and color_by in adata.obs.columns:
        fig = plot_qc_spatial(adata, color_by)
    else:
        import plotly.express as px

        coords = adata.obsm["spatial"]
        fig = px.scatter(x=coords[:, 0], y=coords[:, 1], labels={"x": "x", "y": "y"})
        fig.update_yaxes(autorange="reversed")

    render_interactive_plot(fig, title="Upload spatial map", module="upload", key="upload_spatial_preview")

    if adata.uns.get("spatial"):
        st.caption("Histology images available in uns['spatial'] — overlay in spatial analysis.")


def _render_post_upload_actions() -> None:
    st.markdown("**Next steps**")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Run QC only", key="upload_action_qc"):
        st.session_state.active_module = "spatial_analysis"
        st.session_state.spatial_analysis_qc_only = True
        st.rerun()
    if c2.button("Run Full Spatial Analysis", type="primary", key="upload_action_full"):
        st.session_state.active_module = "spatial_analysis"
        st.session_state.spatial_analysis_run_full = True
        st.rerun()
    if c3.button("Run Discovery Engine", key="upload_action_discovery"):
        st.session_state.active_module = "discovery"
        st.session_state.ribbon_action = "run_discovery"
        st.rerun()
    if c4.button("Generate Report", key="upload_action_report"):
        st.session_state.active_module = "report"
        st.session_state.ribbon_action = "gen_html"
        st.rerun()


def render():
    st.markdown("### Upload & Data")
    st.caption("Universal spatial omics ingestion — Visium, h5ad, CSV matrix + coordinates.")

    result = upload_panel()
    if result.get("adata") is not None or result.get("detection"):
        _store_ingestion(result)

    adata = st.session_state.get("adata")
    ingestion = st.session_state.get("ingestion_result", {})

    if ingestion.get("detection"):
        _render_detection_panel(ingestion["detection"])

    if adata is not None:
        score, status = data_readiness_score(adata)
        platform = st.session_state.get("mbsi_platform", ingestion.get("platform", "unknown"))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spots", f"{adata.n_obs:,}")
        c2.metric("Genes", f"{adata.n_vars:,}")
        c3.metric("Platform", platform)
        c4.metric("Readiness", f"{score}/100", status)

        if "spatial" in adata.obsm:
            _render_spatial_preview(adata)
            safe_register_finding(
                f"Uploaded {platform}: {adata.n_obs} spots, readiness {score}/100",
                section="upload",
                module="upload",
                title="Data loaded",
            )

        compatibility = ingestion.get("compatibility") or result.get("compatibility")
        if compatibility:
            _render_compatibility_panel(compatibility)

        _render_post_upload_actions()
    else:
        st.info("No data loaded yet. Upload Visium ZIP, h5ad, or CSV matrix + coordinates.")

    st.divider()
    if st.button("Load Advanced Demo Instead", key="upload_load_demo"):
        load_advanced_demo_into_session(force=True)
        st.session_state.using_synthetic_demo = True
        st.session_state.mbsi_platform = "demo"
        st.session_state.mbsi_readiness = {"status": "Synthetic demo data"}
        st.rerun()
