"""Upload workspace — real file upload and AnnData assembly."""

from __future__ import annotations

import streamlit as st
import anndata as ad
import numpy as np
import pandas as pd

from app.components.uploaders import data_readiness_score, upload_panel
from app.components.page_utils import load_advanced_demo_into_session
from app.workspaces._helpers import add_finding, safe_register_finding


def build_adata_from_matrix_and_coords(
    count_matrix: pd.DataFrame,
    coordinates: pd.DataFrame,
) -> ad.AnnData:
    """Build AnnData from count matrix (spots × genes) and coordinate table."""
    coords = coordinates.copy()
    if "x" not in coords.columns or "y" not in coords.columns:
        raise ValueError("Coordinates must include 'x' and 'y' columns")

    matrix = count_matrix.copy()
    if matrix.index.intersection(coords.index).size >= max(3, min(len(matrix), len(coords)) // 2):
        shared = matrix.index.intersection(coords.index)
        matrix = matrix.loc[shared]
        coords = coords.loc[shared]
    else:
        n = min(len(matrix), len(coords))
        matrix = matrix.iloc[:n]
        coords = coords.iloc[:n]

    spatial = coords[["x", "y"]].astype(float).values
    adata = ad.AnnData(
        X=matrix.values,
        obs=pd.DataFrame(index=matrix.index.astype(str)),
        var=pd.DataFrame(index=matrix.columns.astype(str)),
    )
    adata.obsm["spatial"] = spatial
    adata.obs["x"] = spatial[:, 0]
    adata.obs["y"] = spatial[:, 1]
    return adata


def _apply_upload_result(result: dict) -> None:
    if result.get("adata") is not None:
        st.session_state.adata = result["adata"]
        st.session_state.using_synthetic_demo = False
    if result.get("image") is not None:
        st.session_state.uploaded_image = result["image"]
    if result.get("segmentation") is not None:
        st.session_state.uploaded_segmentation = result["segmentation"]

    matrix = result.get("count_matrix")
    coords = result.get("coordinates")
    if matrix is not None and coords is not None:
        try:
            adata = build_adata_from_matrix_and_coords(matrix, coords)
            st.session_state.adata = adata
            st.session_state.using_synthetic_demo = False
            st.success(f"Built AnnData from matrix + coords: {adata.n_obs} spots × {adata.n_vars} genes")
        except Exception as exc:
            st.error(f"Could not build AnnData: {exc}")


def render():
    st.markdown("### Upload & Data")
    st.caption("Upload real spatial data — h5ad, CSV matrix + coordinates, image, or segmentation.")

    result = upload_panel()
    _apply_upload_result(result)

    adata = st.session_state.get("adata")
    if adata is not None:
        score, status = data_readiness_score(adata)
        c1, c2, c3 = st.columns(3)
        c1.metric("Spots", f"{adata.n_obs:,}")
        c2.metric("Genes", f"{adata.n_vars:,}")
        c3.metric("Readiness", f"{score}/100", status)

        if "spatial" in adata.obsm:
            coords = adata.obsm["spatial"]
            st.markdown("**Spatial preview**")
            st.scatter_chart(
                pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1]}),
                x="x",
                y="y",
                height=320,
            )
            safe_register_finding(
                f"Uploaded data: {adata.n_obs} spots, readiness {score}/100",
                section="upload",
                module="upload",
                title="Data loaded",
            )

        if st.button("Use Uploaded Data for Analysis", type="primary", key="upload_use_for_analysis"):
            st.session_state.using_synthetic_demo = False
            st.session_state.active_module = "spatial_analysis"
            add_finding("Upload", f"Data ready for analysis ({adata.n_obs} spots)", module="upload")
            st.rerun()
    else:
        st.info("No data loaded yet. Upload h5ad or CSV matrix + coordinates.")

    st.divider()
    if st.button("Load Advanced Demo Instead", key="upload_load_demo"):
        load_advanced_demo_into_session(force=True)
        st.session_state.using_synthetic_demo = True
        st.rerun()
