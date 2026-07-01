"""Segmentation & Registration workspace."""

from __future__ import annotations

import numpy as np
import streamlit as st

from app.components.interactive_figures import render_interactive_plot
from app.components.page_header import render_page_header
from app.components.page_utils import OUTPUT_DIR, init_session
from app.workspaces._helpers import add_finding, safe_register_finding, safe_register_table
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WORKFLOW_SUBSTEPS, WorkflowModule
from mbsi.segmentation.adapters import available_backends, get_technology_segmentation_plan
from mbsi.segmentation.export import import_cell_boundaries, import_segmentation_mask
from mbsi.workflows.segment_register import run_segment_register_workflow


def _init_segmentation_state():
    init_session()
    defaults = {
        "tissue_mask": None,
        "nuclei_mask": None,
        "cell_mask": None,
        "cell_boundaries": None,
        "compartment_labels": None,
        "boundary_map": None,
        "segmentation_qc": None,
        "seg_tissue_method": "otsu",
        "seg_cell_method": "voronoi",
        "seg_compartment_method": "hybrid",
        "seg_source": "run_tissue",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def _ensure_adata():
    adata = st.session_state.get("adata")
    if adata is not None:
        return adata
    st.warning("Segmentation unavailable — upload real data in Study Setup & Data first.")
    st.stop()


def _synthetic_image():
    rng = np.random.default_rng(42)
    img = rng.integers(180, 240, (128, 128, 3), dtype=np.uint8)
    img[20:100, 20:100] = rng.integers(80, 160, (80, 80, 3), dtype=np.uint8)
    return img


def _overlay_preview(image, mask=None, coords=None):
    import plotly.graph_objects as go
    fig = go.Figure()
    if image is not None and image.ndim >= 2:
        gray = image[..., 0] if image.ndim == 3 else image
        fig.add_trace(go.Heatmap(z=gray, colorscale="Gray", showscale=False, opacity=0.85))
    if mask is not None and mask.ndim >= 2:
        fig.add_trace(go.Heatmap(z=mask.astype(float), colorscale="Viridis", showscale=False, opacity=0.35))
    if coords is not None and len(coords):
        fig.add_trace(
            go.Scatter(
                x=coords[:, 0],
                y=coords[:, 1],
                mode="markers",
                marker=dict(size=4, color="red"),
                name="spatial",
            )
        )
    fig.update_layout(
        title="Segmentation overlay",
        xaxis=dict(scaleanchor="y"),
        margin=dict(l=10, r=10, t=40, b=10),
        height=360,
    )
    return fig


def render():
    _init_segmentation_state()
    adata = _ensure_adata()
    tech_key = st.session_state.get("selected_technology") or st.session_state.get("mbsi_platform", "")
    spec = get_technology(tech_key)
    plan = get_technology_segmentation_plan(tech_key)
    backends = available_backends()

    platform_label = spec.label if spec else tech_key or "generic"
    render_page_header(
        "Segmentation & Registration",
        f"Platform: {platform_label} · {plan.get('notes', '')}",
        icon="🔲",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Input status**")
        st.write(f"Observations: {adata.n_obs:,}")
        st.write(f"Image uploaded: {'yes' if st.session_state.get('uploaded_image') is not None else 'no (synthetic H&E used)'}")
        st.write(f"Segmentation QC pass: {st.session_state.get('segmentation_qc', {}).get('qc_pass', '—')}")
    with col2:
        st.markdown("**Available backends**")
        st.write({k: v for k, v in backends.items() if v})

    image = st.session_state.get("uploaded_image")
    if image is None:
        image = _synthetic_image()

    imported_mask = st.session_state.get("tissue_mask")

    substeps = WORKFLOW_SUBSTEPS[WorkflowModule.SEGMENT_REGISTER.value]
    tabs = st.tabs([s.replace("_", " ").title() for s in substeps])

    with tabs[0]:
        st.markdown("#### Tissue mask")
        st.session_state.seg_source = st.selectbox(
            "Segmentation source",
            ["run_tissue", "uploaded", "imported", "voronoi"],
            index=["run_tissue", "uploaded", "imported", "voronoi"].index(
                st.session_state.get("seg_source", "run_tissue")
            ),
            key="seg_source_select",
        )
        tissue_methods = ["otsu", "adaptive"]
        if backends.get("sam"):
            tissue_methods.append("sam")
        st.session_state.seg_tissue_method = st.selectbox(
            "Tissue method", tissue_methods, key="seg_tissue_method_select"
        )
        mask_file = st.file_uploader("Upload tissue mask", type=["npy", "png", "tif"], key="seg_tissue_upload")
        if mask_file is not None:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=mask_file.name) as tmp:
                tmp.write(mask_file.read())
                tmp.flush()
                imported_mask = import_segmentation_mask(tmp.name)
                st.session_state.tissue_mask = imported_mask

    with tabs[1]:
        st.markdown("#### Nuclei / cell segmentation")
        cell_methods = ["voronoi", "watershed", "imported"]
        if backends.get("cellpose"):
            cell_methods.insert(0, "cellpose")
        if backends.get("stardist"):
            cell_methods.insert(1, "stardist")
        st.session_state.seg_cell_method = st.selectbox(
            "Cell/nuclei method", cell_methods, key="seg_cell_method_select"
        )
        boundary_file = st.file_uploader("Import cell boundaries (GeoJSON/CSV)", type=["geojson", "csv"], key="seg_boundary_upload")
        if boundary_file is not None:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=boundary_file.name) as tmp:
                tmp.write(boundary_file.read())
                tmp.flush()
                st.session_state.cell_boundaries = import_cell_boundaries(tmp.name)

    with tabs[2]:
        st.markdown("#### Image registration")
        st.file_uploader("Registration transform / aligned image", key="ws_reg_image")
        st.info("Visium scalefactors, Xenium morphology, CosMx FOV offsets, and Stereo-seq bin coords supported.")

    with tabs[3]:
        st.markdown("#### Compartments & regions")
        st.session_state.seg_compartment_method = st.selectbox(
            "Compartment mode",
            ["hybrid", "histology", "expression"],
            key="seg_compartment_select",
        )
        st.text_area("Region selection notes (lasso / ROI)", key="ws_region_notes")

    coords = np.asarray(adata.obsm["spatial"])
    preview_fig = _overlay_preview(image, st.session_state.get("tissue_mask"), coords)
    render_interactive_plot(preview_fig, title="Segmentation preview", module="segment_register", key="seg_preview")

    if st.button("Run segmentation", type="primary", key="ws_run_segment"):
        with st.spinner("Running segmentation pipeline..."):
            run = run_segment_register_workflow(
                adata,
                technology_key=tech_key,
                image=image,
                tissue_method=st.session_state.seg_tissue_method,
                cell_method=st.session_state.seg_cell_method,
                compartment_method=st.session_state.seg_compartment_method,
                segmentation_source=st.session_state.seg_source,
                imported_mask=imported_mask if st.session_state.seg_source in ("uploaded", "imported") else None,
                out_dir=OUTPUT_DIR,
            )
            st.session_state.run_outputs["segment_register"] = run.to_dict()
            if run.status == "success":
                outs = run.outputs
                st.session_state.tissue_mask = outs.get("tissue_mask")
                st.session_state.nuclei_mask = outs.get("nuclei_mask")
                st.session_state.cell_mask = outs.get("cell_mask")
                st.session_state.compartment_labels = outs.get("compartment_labels")
                st.session_state.boundary_map = outs.get("boundary_map")
                st.session_state.segmentation_qc = outs.get("segmentation_qc")
                if outs.get("adata") is not None:
                    st.session_state.adata = outs["adata"]
                for f in outs.get("segmentation_findings", []):
                    add_finding(f.get("title", "Segmentation finding"), f.get("summary", ""), module="segment_register")
                st.session_state.last_run = "Segmentation & Registration"
                qc = outs.get("segmentation_qc", {})
                metrics = qc.get("metrics", {})
                safe_register_table("segment_register", "segmentation_qc", _qc_dataframe(metrics))
                safe_register_finding(
                    f"Segmentation QC confidence {metrics.get('segmentation_confidence', 0)}",
                    section="segmentation",
                    module="segment_register",
                    title="Segmentation complete",
                )
            st.toast("Segmentation complete." if run.status == "success" else "Segmentation failed.")

    qc = st.session_state.get("segmentation_qc")
    if qc:
        st.markdown("#### Segmentation QC")
        st.json(qc)
        if qc.get("warnings"):
            for w in qc["warnings"]:
                st.warning(w)

    if st.button("Continue to Spatial Analysis →", key="seg_to_spatial"):
        st.session_state.active_module = WorkflowModule.SPATIAL_ANALYSIS.value
        st.rerun()


def _qc_dataframe(metrics: dict):
    import pandas as pd
    if not metrics:
        return pd.DataFrame({"metric": [], "value": []})
    return pd.DataFrame({"metric": list(metrics.keys()), "value": list(metrics.values())})
