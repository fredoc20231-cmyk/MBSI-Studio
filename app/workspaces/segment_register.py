"""Segmentation & Registration workspace."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from app.components.histology_viewer import (
    get_active_histology_image,
    histology_status_caption,
    render_histology_overlay,
    sync_histology_session_from_adata,
)
from app.components.interactive_figures import render_interactive_plot
from app.components.page_header import render_page_header
from app.components.page_utils import OUTPUT_DIR, init_session
from app.workspaces._helpers import add_finding, safe_register_finding, safe_register_table
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WORKFLOW_SUBSTEPS, WorkflowModule
from mbsi.segmentation.adapters import (
    available_backends,
    baseline_unet_available,
    cellpose_available,
    mesmer_available,
    stardist_available,
)
from mbsi.segmentation.baseline_unet import UNTRAINED_MESSAGE
from mbsi.segmentation.export import export_boundaries, export_label_mask, import_cell_boundaries, import_segmentation_mask
from mbsi.workflows.segment_register import run_segment_register_workflow

SEGMENTATION_METHODS = [
    "imported_boundaries",
    "stardist_expansion",
    "cellpose",
    "omnipose",
    "mesmer",
    "baseline_unet",
    "watershed",
    "voronoi",
]
CHANNEL_OPTIONS = ["grayscale", "red", "green", "blue", "dapi"]


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
        "seg_cell_method": "imported_boundaries",
        "seg_compartment_method": "hybrid",
        "seg_source": "run_tissue",
        "seg_expansion_pixels": 5,
        "seg_channel": "grayscale",
        "seg_transcript_df": None,
        "seg_boundary_path": None,
        "seg_imported_mask": None,
        "seg_export_paths": {},
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def _ensure_adata():
    adata = st.session_state.get("adata")
    if adata is not None:
        return adata
    st.warning("Segmentation unavailable — upload real data in Study Setup & Data first.")
    st.stop()


def _qc_dataframe(metrics: dict):
    if not metrics:
        return pd.DataFrame({"metric": [], "value": []})
    return pd.DataFrame({"metric": list(metrics.keys()), "value": list(metrics.values())})


def _method_needs_image(method: str) -> bool:
    return method in (
        "stardist_expansion",
        "cellpose",
        "omnipose",
        "mesmer",
        "baseline_unet",
        "watershed",
    )


def _method_needs_input(method: str, image, imported_mask, boundary_uploaded) -> bool:
    if method == "imported_boundaries":
        return imported_mask is not None or boundary_uploaded
    if method == "voronoi":
        return True
    return image is not None


def render():
    _init_segmentation_state()
    adata = _ensure_adata()
    sync_histology_session_from_adata(adata)
    tech_key = st.session_state.get("selected_technology") or st.session_state.get("mbsi_platform", "")
    spec = get_technology(tech_key)
    backends = available_backends()

    platform_label = spec.label if spec else tech_key or "generic"
    render_page_header(
        "Segmentation & Registration",
        f"Platform: {platform_label} · High-resolution cell boundary segmentation",
        icon="🔲",
    )

    image, image_source = get_active_histology_image(adata)
    st.markdown(histology_status_caption(adata), unsafe_allow_html=True)

    xenium_status = adata.uns.get("mbsi_segmentation", {}).get("segmentation_status")
    if xenium_status:
        st.info(xenium_status)

    st.markdown("#### Upload inputs")
    up_col1, up_col2 = st.columns(2)
    with up_col1:
        morph_upload = st.file_uploader(
            "Upload DAPI / H&E / morphology image",
            type=["png", "jpg", "jpeg", "tif", "tiff", "ome.tif", "ome.tiff"],
            key="seg_morphology_upload",
        )
        mask_file = st.file_uploader(
            "Upload existing segmentation mask",
            type=["npy", "png", "tif", "tiff"],
            key="seg_mask_upload",
        )
    with up_col2:
        boundary_file = st.file_uploader(
            "Upload boundary file (GeoJSON / CSV / parquet)",
            type=["geojson", "csv", "parquet", "gz"],
            key="seg_boundary_upload",
        )
        transcript_file = st.file_uploader(
            "Upload transcripts file (CSV / parquet)",
            type=["csv", "parquet", "gz"],
            key="seg_transcript_upload",
        )

    if morph_upload is not None:
        from PIL import Image

        st.session_state.uploaded_image = np.asarray(Image.open(morph_upload).convert("RGB"))
        st.session_state.histology_source = "Uploaded image (Segmentation page)"
        image, image_source = get_active_histology_image(adata)
        st.success("Morphology image stored for segmentation and visualization.")

    imported_mask = st.session_state.get("seg_imported_mask")
    if mask_file is not None:
        with tempfile.NamedTemporaryFile(suffix=Path(mask_file.name).suffix) as tmp:
            tmp.write(mask_file.read())
            tmp.flush()
            imported_mask = import_segmentation_mask(tmp.name)
            st.session_state.seg_imported_mask = imported_mask
            st.session_state.tissue_mask = imported_mask
            st.success(f"Imported mask: shape {imported_mask.shape}, max label {imported_mask.max()}")

    boundary_path = st.session_state.get("seg_boundary_path")
    if boundary_file is not None:
        suffix = Path(boundary_file.name).suffix or ".csv"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(boundary_file.read())
            tmp.flush()
            boundary_path = tmp.name
            st.session_state.seg_boundary_path = boundary_path
            st.session_state.cell_boundaries = import_cell_boundaries(boundary_path)
            st.success("Boundary file stored for import.")

    transcript_df = st.session_state.get("seg_transcript_df")
    if transcript_file is not None:
        try:
            if transcript_file.name.endswith(".parquet"):
                transcript_df = pd.read_parquet(transcript_file)
            else:
                transcript_df = pd.read_csv(transcript_file)
            st.session_state.seg_transcript_df = transcript_df
            st.success(f"Loaded {len(transcript_df):,} transcripts")
        except Exception as exc:
            st.error(f"Failed to load transcripts: {exc}")

    st.markdown("#### Segmentation settings")
    set_col1, set_col2, set_col3 = st.columns(3)
    with set_col1:
        method_options = list(SEGMENTATION_METHODS)
        current_method = st.session_state.get("seg_cell_method", "imported_boundaries")
        if current_method not in method_options:
            current_method = "voronoi"
        st.session_state.seg_cell_method = st.selectbox(
            "Segmentation method",
            method_options,
            index=method_options.index(current_method),
            format_func=lambda x: x.replace("_", " ").title(),
            key="seg_method_select",
        )
    with set_col2:
        st.session_state.seg_channel = st.selectbox(
            "Channel",
            CHANNEL_OPTIONS,
            index=CHANNEL_OPTIONS.index(st.session_state.get("seg_channel", "grayscale")),
            key="seg_channel_select",
        )
    with set_col3:
        st.session_state.seg_expansion_pixels = st.slider(
            "Expansion pixels (StarDist)",
            min_value=1,
            max_value=30,
            value=int(st.session_state.get("seg_expansion_pixels", 5)),
            key="seg_expansion_slider",
        )

    method = st.session_state.seg_cell_method
    if method == "stardist_expansion" and not stardist_available():
        st.warning("StarDist is not installed. Install with: `pip install stardist tensorflow`")
    if method in ("cellpose", "omnipose") and not cellpose_available():
        st.warning("Cellpose/Omnipose is not installed. Install with: `pip install cellpose`")
    if method == "mesmer" and not mesmer_available():
        st.warning("DeepCell Mesmer is not installed. Install with: `pip install deepcell`")
    if method == "baseline_unet" and not baseline_unet_available():
        st.warning(UNTRAINED_MESSAGE)

    map_transcripts = st.checkbox(
        "Map transcripts to cells (requires transcripts file)",
        value=False,
        key="seg_map_transcripts",
    )
    if map_transcripts and transcript_df is None:
        st.warning("Transcript mapping requested but no transcripts file uploaded.")

    st.markdown("#### Input status")
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        st.write(f"Observations: {adata.n_obs:,}")
        st.write(f"Histology: {image_source}")
        st.write(f"Mask uploaded: {'yes' if imported_mask is not None else 'no'}")
        st.write(f"Boundary file: {'yes' if boundary_path else 'no'}")
    with status_col2:
        st.write(f"Transcripts: {len(transcript_df):,}" if transcript_df is not None else "Transcripts: none")
        st.write(
            {
                k: v
                for k, v in backends.items()
                if v
                and k in ("cellpose", "stardist", "mesmer", "baseline_unet", "watershed", "voronoi")
            }
        )

    if not _method_needs_input(method, image, imported_mask, bool(boundary_path)):
        if method == "imported_boundaries":
            st.warning("Upload an existing mask or boundary file for imported boundaries.")
        elif _method_needs_image(method):
            st.warning("Upload a morphology image to run image-based segmentation.")

    substeps = WORKFLOW_SUBSTEPS[WorkflowModule.SEGMENT_REGISTER.value]
    tabs = st.tabs([s.replace("_", " ").title() for s in substeps])

    with tabs[0]:
        st.markdown("#### Tissue mask (optional)")
        st.session_state.seg_tissue_method = st.selectbox(
            "Tissue method", ["otsu", "adaptive"], key="seg_tissue_method_select"
        )

    with tabs[1]:
        st.markdown("#### Cell boundary method")
        st.caption("Production mode uses real uploads only — no synthetic segmentation.")

    with tabs[2]:
        st.markdown("#### Image registration")
        st.file_uploader("Registration transform / aligned image", key="ws_reg_image")
        st.info("Visium scalefactors, Xenium morphology, CosMx FOV offsets supported.")

    with tabs[3]:
        st.markdown("#### Compartments & regions")
        st.session_state.seg_compartment_method = st.selectbox(
            "Compartment mode",
            ["hybrid", "histology", "expression"],
            key="seg_compartment_select",
        )

    coords = np.asarray(adata.obsm["spatial"]) if "spatial" in adata.obsm else None
    preview_mask = st.session_state.get("cell_mask")
    if image is not None and coords is not None:
        preview_fig = render_histology_overlay(
            adata=adata,
            image=image,
            color="total_counts" if "total_counts" in adata.obs.columns else None,
            title="Segmentation overlay preview",
            show_image=True,
            show_spots=True,
            image_source=image_source,
            return_figure=True,
        )
        overlay = preview_mask if preview_mask is not None and getattr(preview_mask, "ndim", 0) >= 2 else st.session_state.get("tissue_mask")
        if overlay is not None and getattr(overlay, "ndim", 0) >= 2:
            import plotly.graph_objects as go

            preview_fig.add_trace(
                go.Heatmap(
                    z=np.asarray(overlay, dtype=float),
                    colorscale="Viridis",
                    showscale=False,
                    opacity=0.35,
                )
            )
    else:
        import plotly.graph_objects as go

        preview_fig = go.Figure()
        if coords is not None:
            preview_fig.add_trace(
                go.Scattergl(
                    x=coords[:, 0],
                    y=coords[:, 1],
                    mode="markers",
                    marker=dict(size=4, color="#4f7cff"),
                )
            )
        preview_fig.update_layout(title="Segmentation preview (coordinates only)", height=360)
        preview_fig.update_yaxes(autorange="reversed")

    render_interactive_plot(preview_fig, title="Segmentation overlay preview", module="segment_register", key="seg_preview")

    run_disabled = not _method_needs_input(method, image, imported_mask, bool(boundary_path))
    if method == "stardist_expansion" and not stardist_available():
        run_disabled = True
    if method in ("cellpose", "omnipose") and not cellpose_available():
        run_disabled = True
    if method == "mesmer" and not mesmer_available():
        run_disabled = True
    if method == "baseline_unet" and not baseline_unet_available():
        run_disabled = True

    if st.button("Run segmentation", type="primary", key="ws_run_segment", disabled=run_disabled):
        with st.spinner("Running segmentation pipeline..."):
            run = run_segment_register_workflow(
                adata,
                technology_key=tech_key,
                image=image,
                tissue_method=st.session_state.seg_tissue_method,
                cell_method=method,
                compartment_method=st.session_state.seg_compartment_method,
                segmentation_source=st.session_state.seg_source,
                imported_mask=imported_mask,
                boundary_path=boundary_path,
                transcript_df=transcript_df,
                expansion_pixels=int(st.session_state.seg_expansion_pixels),
                channel=st.session_state.seg_channel,
                map_transcripts=map_transcripts,
                out_dir=OUTPUT_DIR,
                allow_synthetic_image=False,
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
                st.session_state.seg_export_paths = outs.get("export_paths", {})
                if outs.get("adata") is not None:
                    st.session_state.adata = outs["adata"]
                for w in run.warnings:
                    st.warning(w)
                for f in outs.get("segmentation_findings", []):
                    add_finding(f.get("title", "Segmentation finding"), f.get("summary", ""), module="segment_register")
                st.session_state.last_run = "Segmentation & Registration"
                qc = outs.get("segmentation_qc", {})
                metrics = qc.get("metrics", qc)
                safe_register_table("segment_register", "segmentation_qc", _qc_dataframe(metrics))
                safe_register_finding(
                    f"Segmentation QC confidence {metrics.get('segmentation_confidence', metrics.get('n_cells', '—'))}",
                    section="segmentation",
                    module="segment_register",
                    title="Segmentation complete",
                )
            else:
                st.error(run.error or "Segmentation failed")
            st.toast("Segmentation complete." if run.status == "success" else "Segmentation failed.")

    qc = st.session_state.get("segmentation_qc")
    if qc:
        st.markdown("#### Segmentation QC")
        metrics = qc.get("metrics", qc)
        st.dataframe(_qc_dataframe(metrics), use_container_width=True, hide_index=True)
        if qc.get("warnings"):
            for w in qc["warnings"]:
                st.warning(w)

    export_paths = st.session_state.get("seg_export_paths", {})
    dl_col1, dl_col2 = st.columns(2)
    cell_mask = st.session_state.get("cell_mask")
    with dl_col1:
        if cell_mask is not None and getattr(cell_mask, "ndim", 0) >= 2:
            mask_bytes = io.BytesIO()
            np.save(mask_bytes, cell_mask)
            st.download_button(
                "Download mask (.npy)",
                data=mask_bytes.getvalue(),
                file_name="segmentation_mask.npy",
                mime="application/octet-stream",
                key="seg_download_mask",
            )
        elif export_paths.get("cells"):
            st.download_button(
                "Download mask (.npy)",
                data=Path(export_paths["cells"]).read_bytes(),
                file_name="segmentation_mask.npy",
                mime="application/octet-stream",
                key="seg_download_mask_file",
            )
    with dl_col2:
        if cell_mask is not None and getattr(cell_mask, "ndim", 0) >= 2:
            with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                export_boundaries(tmp.name, label_mask=cell_mask)
                boundary_bytes = Path(tmp.name).read_bytes()
            st.download_button(
                "Download boundaries (.parquet)",
                data=boundary_bytes,
                file_name="cell_boundaries.parquet",
                mime="application/octet-stream",
                key="seg_download_boundaries",
            )
        elif export_paths.get("boundaries"):
            st.download_button(
                "Download boundaries (.parquet)",
                data=Path(export_paths["boundaries"]).read_bytes(),
                file_name="cell_boundaries.parquet",
                mime="application/octet-stream",
                key="seg_download_boundaries_file",
            )

    if st.button("Continue to Spatial Analysis →", key="seg_to_spatial"):
        st.session_state.active_module = WorkflowModule.SPATIAL_ANALYSIS.value
        st.rerun()
