"""File upload components — delegates ingestion to mbsi.io."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import anndata as ad
import numpy as np
import pandas as pd
import streamlit as st

from mbsi.io.compatibility import get_compatibility_matrix
from mbsi.io.detect import detect_platform
from mbsi.io.generic import ingest_csv_matrix_coords, ingest_h5ad
from mbsi.io.ingest import ingest_upload, save_upload_to_temp
from mbsi.io.stereo_seq import load_stereo_seq_dataset
from mbsi.io.validators import compute_readiness


def data_readiness_score(adata) -> Tuple[int, str]:
    """Compute readiness score via mbsi.io validators."""
    if adata is None:
        return 0, "No data loaded"
    score = adata.uns.get("mbsi_readiness_score")
    readiness = adata.uns.get("mbsi_readiness", {})
    if score is not None:
        return int(score), readiness.get("status", "Unknown")
    score, details = compute_readiness(adata)
    return score, details.get("status", "Unknown")


def h5ad_uploader() -> Optional[Dict[str, Any]]:
    uploaded_file = st.file_uploader("Upload h5ad file", type=["h5ad"], key="h5ad_uploader")
    if uploaded_file is None:
        return None
    try:
        temp_path = save_upload_to_temp(uploaded_file, ".h5ad")
        names = [uploaded_file.name]
        detection = detect_platform(names)
        adata, meta = ingest_h5ad(temp_path)
        st.success(f"Loaded: {adata.n_obs} spots, {adata.n_vars} genes")
        return {"adata": adata, "detection": detection, **meta}
    except Exception as exc:
        st.error(f"Error loading h5ad: {exc}")
        return None


def visium_uploader() -> Optional[Dict[str, Any]]:
    uploaded_file = st.file_uploader(
        "Upload Space Ranger outs folder as ZIP",
        type=["zip"],
        key="visium_zip_uploader",
    )
    if uploaded_file is None:
        return None
    try:
        temp_path = save_upload_to_temp(uploaded_file, ".zip")
        result = ingest_upload(visium_path=temp_path, file_names=[uploaded_file.name])
        if result.get("adata") is None:
            st.error("Could not load Visium bundle from ZIP")
            return None
        adata = result["adata"]
        st.success(f"Visium loaded: {adata.n_obs} spots × {adata.n_vars} genes")
        return result
    except Exception as exc:
        st.error(f"Visium load failed: {exc}")
        return None


def csv_matrix_uploader() -> Optional[pd.DataFrame]:
    uploaded_file = st.file_uploader("Upload count matrix CSV", type=["csv"], key="csv_matrix_uploader")
    if uploaded_file is None:
        return None
    try:
        df = pd.read_csv(uploaded_file, index_col=0)
        st.success(f"Loaded matrix: {df.shape[0]} × {df.shape[1]}")
        return df
    except Exception as exc:
        st.error(f"Error loading CSV: {exc}")
        return None


def coordinates_uploader() -> Optional[pd.DataFrame]:
    uploaded_file = st.file_uploader(
        "Upload spatial coordinates CSV (x, y columns)",
        type=["csv"],
        key="coords_uploader",
    )
    if uploaded_file is None:
        return None
    try:
        df = pd.read_csv(uploaded_file)
        if "x" not in df.columns or "y" not in df.columns:
            st.error("CSV must contain 'x' and 'y' columns")
            return None
        st.success(f"Loaded {len(df)} coordinate pairs")
        return df
    except Exception as exc:
        st.error(f"Error loading coordinates: {exc}")
        return None


def image_uploader() -> Optional[np.ndarray]:
    uploaded_file = st.file_uploader(
        "Upload tissue image",
        type=["png", "jpg", "jpeg", "tif", "tiff"],
        key="image_uploader",
    )
    if uploaded_file is None:
        return None
    try:
        from PIL import Image

        image_array = np.array(Image.open(uploaded_file))
        st.success(f"Loaded image: {image_array.shape}")
        return image_array
    except Exception as exc:
        st.error(f"Error loading image: {exc}")
        return None


def segmentation_uploader() -> Optional[np.ndarray]:
    uploaded_file = st.file_uploader(
        "Upload segmentation mask",
        type=["png", "tif", "tiff"],
        key="segmentation_uploader",
    )
    if uploaded_file is None:
        return None
    try:
        from PIL import Image

        mask_array = np.array(Image.open(uploaded_file))
        st.success(f"Loaded mask: {mask_array.shape}")
        return mask_array
    except Exception as exc:
        st.error(f"Error loading mask: {exc}")
        return None


def stereo_seq_uploader() -> Optional[Dict[str, Any]]:
    uploaded = st.file_uploader(
        "Upload Stereo-seq folder as ZIP (GEF/CGEF, SAW, or CSV exports)",
        type=["zip"],
        key="stereo_seq_zip_uploader",
    )
    if uploaded is None:
        return None
    try:
        temp_path = save_upload_to_temp(uploaded, ".zip")
        result = ingest_upload(stereo_seq_path=temp_path, file_names=[uploaded.name])
        if result.get("adata") is None:
            st.error("Could not load Stereo-seq bundle from ZIP")
            return None
        adata = result["adata"]
        lim = result.get("limitations") or result.get("stereo_seq", {}).get("limitations", [])
        st.success(f"Stereo-seq loaded: {adata.n_obs:,} obs × {adata.n_vars} genes")
        if lim:
            st.warning("Partial load: " + "; ".join(lim))
        return result
    except Exception as exc:
        st.error(f"Stereo-seq load failed: {exc}")
        return None


def upload_panel() -> dict:
    """Complete upload panel with platform detection and mbsi.io ingestion."""
    st.subheader("Data Upload")

    data: Dict[str, Any] = {}
    tab_h5, tab_visium, tab_stereo, tab_csv, tab_coords, tab_img, tab_seg = st.tabs(
        ["h5ad", "Visium ZIP", "Stereo-seq ZIP", "CSV Matrix", "Coordinates", "Image", "Segmentation"]
    )

    with tab_h5:
        h5_result = h5ad_uploader()
        if h5_result:
            data.update(h5_result)

    with tab_visium:
        visium_result = visium_uploader()
        if visium_result:
            data.update(visium_result)

    with tab_stereo:
        stereo_result = stereo_seq_uploader()
        if stereo_result:
            data.update(stereo_result)

    with tab_csv:
        data["count_matrix"] = csv_matrix_uploader()

    with tab_coords:
        data["coordinates"] = coordinates_uploader()

    with tab_img:
        data["image"] = image_uploader()

    with tab_seg:
        data["segmentation"] = segmentation_uploader()

    matrix = data.get("count_matrix")
    coords = data.get("coordinates")
    if matrix is not None and coords is not None and data.get("adata") is None:
        try:
            adata, meta = ingest_csv_matrix_coords(matrix, coords)
            data["adata"] = adata
            data.update(meta)
            st.success(f"Built AnnData: {adata.n_obs} spots × {adata.n_vars} genes")
        except Exception as exc:
            st.error(f"Matrix + coords ingest failed: {exc}")

    adata = data.get("adata")
    if adata is not None:
        detection = data.get("detection") or detect_platform([getattr(adata, "filename", "upload.h5ad")])
        score, status = data_readiness_score(adata)
        compatibility = data.get("compatibility") or get_compatibility_matrix(adata, detection)
        data["readiness_score"] = score
        data["readiness"] = adata.uns.get("mbsi_readiness", {"status": status})
        data["compatibility"] = compatibility
        data["platform"] = adata.uns.get("mbsi_platform", detection.get("platform", "unknown"))
        data["detection"] = detection

    return data
