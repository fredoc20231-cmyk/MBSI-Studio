"""
Upload components — universal spatial omics front door.

Supports: 10x Visium, Xenium, MERFISH/MERSCOPE, CosMx, CODEX,
          generic h5ad, CSV matrix + coordinates.

All uploads produce an AnnData satisfying the MBSI internal contract
(adata.uns['mbsi_platform'] + adata.uns['mbsi_readiness']).
"""

from __future__ import annotations

import io
import tempfile
from typing import Dict, Optional, Tuple

import anndata as ad
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from mbsi.io import (
    detect_platform,
    compute_compatibility_matrix,
    load_h5ad,
    load_csv_matrix,
    load_visium_zip,
    load_xenium_zip,
    load_merfish_zip,
    load_cosmx_zip,
    load_codex_zip,
    load_zip,
)
from mbsi.io.converters import compute_readiness


# ---------------------------------------------------------------------------
# Platform picker
# ---------------------------------------------------------------------------

PLATFORM_OPTIONS = {
    "Auto-detect (recommended)": "auto",
    "10x Visium / Visium HD (ZIP)": "visium",
    "10x Xenium (ZIP)": "xenium",
    "MERFISH / MERSCOPE (ZIP)": "merfish",
    "NanoString CosMx (ZIP)": "cosmx",
    "CODEX / PhenoCycler (ZIP)": "codex",
    "AnnData .h5ad": "h5ad",
    "CSV matrix + coordinates": "csv",
}

PLATFORM_DESCRIPTIONS = {
    "visium": "55 µm capture spots • bulk-deconvolution input • H&E + expression",
    "xenium": "Single-cell in-situ sequencing • subcellular transcripts • cell boundaries",
    "merfish": "MERFISH / MERSCOPE • single-cell • molecule coordinates • cell boundaries",
    "cosmx": "NanoString CosMx • ~1000 gene panel • FOV-based • protein optional",
    "codex": "Multiplexed protein imaging • cell segmentation • cyclic IF",
    "h5ad": "Standard AnnData with obsm['spatial'] spatial coordinates",
    "csv": "Count matrix CSV paired with spatial coordinates CSV",
    "auto": "Platform detected from uploaded file names",
}


# ---------------------------------------------------------------------------
# Main upload panel
# ---------------------------------------------------------------------------

def upload_panel() -> Dict:
    """
    Render the universal upload workspace.

    Returns dict with keys: adata, image, segmentation, ground_truth,
    platform, detection_result.
    """
    result: Dict = {
        "adata": None,
        "image": None,
        "segmentation": None,
        "ground_truth": None,
        "platform": None,
        "detection_result": None,
    }

    # --- Platform selector ---
    platform_label = st.selectbox(
        "Data platform",
        list(PLATFORM_OPTIONS.keys()),
        key="platform_selector",
        help="Select your spatial omics platform, or use Auto-detect.",
    )
    chosen_platform = PLATFORM_OPTIONS[platform_label]

    if chosen_platform in PLATFORM_DESCRIPTIONS:
        st.caption(f"ℹ {PLATFORM_DESCRIPTIONS[chosen_platform]}")

    st.divider()

    # --- Route to correct upload widget ---
    if chosen_platform in ("auto", "visium", "xenium", "merfish", "cosmx", "codex"):
        adata = _zip_upload_panel(chosen_platform, result)
    elif chosen_platform == "h5ad":
        adata = _h5ad_upload_panel()
    elif chosen_platform == "csv":
        adata = _csv_upload_panel()
    else:
        adata = _zip_upload_panel("auto", result)

    result["adata"] = adata

    # --- Optional: supplementary files ---
    if adata is not None:
        st.divider()
        with st.expander("Optional: histology image / segmentation / ground truth", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                result["image"] = _image_upload("tissue_image")
            with c2:
                result["segmentation"] = _mask_upload("seg_mask")
            with c3:
                result["ground_truth"] = _h5ad_ground_truth_upload()

    return result


# ---------------------------------------------------------------------------
# Platform-specific upload widgets
# ---------------------------------------------------------------------------

def _zip_upload_panel(platform: str, result: Dict) -> Optional[ad.AnnData]:
    """Upload a ZIP archive (or single h5ad) and auto-detect / load."""
    accept = ["zip", "h5ad", "h5", "gz"]
    label = "Upload data archive (ZIP recommended)"
    if platform == "visium":
        label = "Upload Space Ranger output folder as ZIP"
        st.markdown(
            "**Required inside ZIP:** `filtered_feature_bc_matrix.h5` + `spatial/tissue_positions[_list].csv`"
        )
    elif platform == "xenium":
        label = "Upload Xenium output folder as ZIP"
        st.markdown(
            "**Required:** `cell_feature_matrix.h5` + `cells.csv[.gz]`  "
            "— Optional: `transcripts.csv`, `cell_boundaries.csv`, morphology image"
        )
    elif platform == "merfish":
        label = "Upload MERSCOPE output folder as ZIP"
        st.markdown("**Required:** `cell_by_gene.csv` + `cell_metadata.csv`")
    elif platform == "cosmx":
        label = "Upload CosMx output folder as ZIP"
        st.markdown("**Required:** `*_exprMat_file.csv` + `*_metadata_file.csv`")
    elif platform == "codex":
        label = "Upload CODEX / PhenoCycler output as ZIP"
        st.markdown("**Required:** `cell_table.csv`  — Optional: `channel_names.txt`")

    uploaded = st.file_uploader(label, type=accept, key=f"zip_uploader_{platform}")
    if uploaded is None:
        return None

    # Auto-detect from file names inside ZIP if platform is 'auto'
    if platform == "auto" and uploaded.name.endswith(".zip"):
        import zipfile as _zipfile
        raw = uploaded.read()
        with _zipfile.ZipFile(io.BytesIO(raw), "r") as z:
            file_names = z.namelist()
        det = detect_platform(file_names)
        result["detection_result"] = det
        platform = det.platform or "h5ad"
        _render_detection_banner(det)
        file_bytes = io.BytesIO(raw)
    else:
        file_bytes = io.BytesIO(uploaded.read())

    with st.spinner(f"Loading {uploaded.name} …"):
        try:
            loaders = {
                "visium": load_visium_zip,
                "xenium": load_xenium_zip,
                "merfish": load_merfish_zip,
                "cosmx": load_cosmx_zip,
                "codex": load_codex_zip,
            }
            if uploaded.name.endswith(".h5ad"):
                adata = load_h5ad(file_bytes)
            elif platform in loaders:
                adata = loaders[platform](file_bytes)
            else:
                adata = load_zip(file_bytes)

            result["platform"] = adata.uns.get("mbsi_platform", {}).get("platform", platform)
            st.success(
                f"Loaded: {adata.n_obs:,} spots/cells × {adata.n_vars:,} genes/markers"
            )
            return adata

        except Exception as exc:
            st.error(f"Failed to load `{uploaded.name}`: {exc}")
            with st.expander("Full error"):
                import traceback
                st.code(traceback.format_exc())
            return None


def _h5ad_upload_panel() -> Optional[ad.AnnData]:
    uploaded = st.file_uploader("Upload .h5ad file", type=["h5ad"], key="h5ad_up")
    if uploaded is None:
        return None
    with st.spinner("Reading h5ad …"):
        try:
            adata = load_h5ad(uploaded)
            st.success(f"Loaded: {adata.n_obs:,} obs × {adata.n_vars:,} vars")
            return adata
        except Exception as exc:
            st.error(f"Could not read h5ad: {exc}")
            return None


def _csv_upload_panel() -> Optional[ad.AnnData]:
    st.markdown(
        "Upload a count matrix CSV (rows = cells/spots, columns = genes) "
        "and a coordinates CSV."
    )
    c1, c2 = st.columns(2)
    with c1:
        counts_file = st.file_uploader("Count matrix CSV", type=["csv", "tsv"], key="csv_counts")
    with c2:
        coords_file = st.file_uploader(
            "Coordinates CSV (x, y columns)", type=["csv"], key="csv_coords"
        )

    if counts_file is None:
        return None
    with st.spinner("Loading CSV …"):
        try:
            sep = "\t" if counts_file.name.endswith(".tsv") else ","
            adata = load_csv_matrix(counts_file, coords_source=coords_file, separator=sep)
            st.success(f"Loaded: {adata.n_obs:,} obs × {adata.n_vars:,} vars")
            return adata
        except Exception as exc:
            st.error(f"CSV load failed: {exc}")
            return None


def _image_upload(key: str) -> Optional[np.ndarray]:
    f = st.file_uploader(
        "Histology image", type=["png", "jpg", "jpeg", "tif", "tiff"], key=key
    )
    if f is None:
        return None
    try:
        from PIL import Image
        return np.array(Image.open(f))
    except Exception as exc:
        st.warning(f"Image load failed: {exc}")
        return None


def _mask_upload(key: str) -> Optional[np.ndarray]:
    f = st.file_uploader("Segmentation mask", type=["png", "tif", "tiff"], key=key)
    if f is None:
        return None
    try:
        from PIL import Image
        return np.array(Image.open(f))
    except Exception as exc:
        st.warning(f"Mask load failed: {exc}")
        return None


def _h5ad_ground_truth_upload() -> Optional[ad.AnnData]:
    f = st.file_uploader("Ground truth h5ad", type=["h5ad"], key="gt_h5ad")
    if f is None:
        return None
    try:
        return load_h5ad(f)
    except Exception as exc:
        st.warning(f"Ground truth load failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Detection banner
# ---------------------------------------------------------------------------

def _render_detection_banner(det) -> None:
    color = (
        "#39d98a" if det.confidence >= 0.8
        else "#ffb020" if det.confidence >= 0.5
        else "#ff5c7a"
    )
    confidence_pct = int(det.confidence * 100)
    st.markdown(
        f"""
        <div style="background:#0d1828;border:1px solid {color};border-radius:8px;
                    padding:12px 16px;margin:8px 0;">
          <div style="font-size:0.85rem;font-weight:700;color:{color};">
            Dataset detected: {det.display_name}
          </div>
          <div style="font-size:0.75rem;color:#9aa7b8;margin-top:4px;">
            {det.notes}  ·  Detection confidence: {confidence_pct}%
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if det.files_missing:
        st.warning(f"Expected files not found: {', '.join(det.files_missing)}")
    if det.files_optional_found:
        st.caption(f"Optional files found: {', '.join(det.files_optional_found)}")


# ---------------------------------------------------------------------------
# Readiness + compatibility panel
# ---------------------------------------------------------------------------

def render_readiness_panel(adata: ad.AnnData) -> None:
    """
    Render the readiness score, capability flags, and compatibility matrix.
    Called from the Upload page after a successful load.
    """
    readiness = adata.uns.get("mbsi_readiness") or compute_readiness(adata)
    platform_meta = adata.uns.get("mbsi_platform", {})

    score = readiness["score"]
    status = readiness["status"]
    caps = readiness["capabilities"]

    # Score strip
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Readiness Score", f"{score}/100", status)
    c2.metric("Spots / Cells", f"{adata.n_obs:,}")
    c3.metric("Genes / Markers", f"{adata.n_vars:,}")
    c4.metric("Platform", platform_meta.get("display_name", "Unknown"))

    for issue in readiness.get("issues", []):
        st.error(f"✗ {issue}")
    for w in readiness.get("warnings", []):
        st.warning(f"⚠ {w}")

    st.divider()
    st.markdown("#### Available Analyses")

    compat = compute_compatibility_matrix(
        adata_present=caps.get("expression_matrix", False),
        has_spatial=caps.get("spatial_coords", False),
        has_gene_names=caps.get("gene_names", False),
        has_cell_types=caps.get("cell_types", False),
        has_ground_truth=False,
        is_spot_platform=platform_meta.get("coordinate_type") == "spot",
    )

    avail_cols = st.columns(3)
    available = [(k, v) for k, v in compat.items() if v["available"]]
    unavailable = [(k, v) for k, v in compat.items() if not v["available"]]

    with avail_cols[0]:
        st.markdown("**✓ Available**")
        for name, info in available:
            st.markdown(
                f'<div style="color:#39d98a;font-size:0.8rem;margin:2px 0;">● {name}</div>',
                unsafe_allow_html=True,
            )
            st.caption(info["reason"])

    with avail_cols[1]:
        st.markdown("**✗ Unavailable**")
        for name, info in unavailable:
            st.markdown(
                f'<div style="color:#ff5c7a;font-size:0.8rem;margin:2px 0;">✗ {name}</div>',
                unsafe_allow_html=True,
            )
            st.caption(info["reason"])

    with avail_cols[2]:
        _readiness_gauge(score)

    st.divider()

    if caps.get("spatial_coords"):
        render_spatial_preview(adata)


def _readiness_gauge(score: int) -> None:
    color = "#39d98a" if score >= 85 else "#ffb020" if score >= 60 else "#ff5c7a"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        number={"suffix": "/100", "font": {"color": "#f4f7fb", "size": 22}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#9aa7b8"},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "#0d1828",
            "bordercolor": "#22314a",
            "steps": [
                {"range": [0, 50], "color": "#1a1f2e"},
                {"range": [50, 80], "color": "#152033"},
                {"range": [80, 100], "color": "#0d2040"},
            ],
        },
        title={"text": "Readiness", "font": {"color": "#9aa7b8", "size": 13}},
    ))
    fig.update_layout(
        height=180, margin=dict(t=30, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", font_color="#f4f7fb",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------------------------------------------------------------------
# Interactive spatial preview
# ---------------------------------------------------------------------------

def render_spatial_preview(
    adata: ad.AnnData,
    color_by: Optional[str] = None,
    max_points: int = 10_000,
) -> None:
    """
    Render an interactive Plotly spatial map of the loaded dataset.

    Parameters
    ----------
    adata : AnnData
    color_by : str or None
        obs column to colour by. If None, offers a selectbox.
    max_points : int
        Rendering cap.
    """
    coords = adata.obsm["spatial"]
    n_total = len(coords)
    idx = (
        np.random.choice(n_total, max_points, replace=False)
        if n_total > max_points
        else np.arange(n_total)
    )
    x = coords[idx, 0]
    y = coords[idx, 1]

    colour_options = ["None"] + [
        c for c in adata.obs.columns
        if adata.obs[c].dtype.name in ("category", "object") or "type" in c.lower()
    ]

    col_ctrl, col_gene = st.columns(2)
    with col_ctrl:
        if color_by is None:
            color_by = st.selectbox(
                "Colour by obs column", colour_options, key="preview_color"
            )
        if color_by == "None":
            color_by = None

    gene_expr = None
    with col_gene:
        gene_sel = st.selectbox(
            "Show gene expression",
            ["None"] + list(adata.var_names[:300]),
            key="preview_gene",
        )
        if gene_sel != "None":
            import scipy.sparse as sp
            col_idx = list(adata.var_names).index(gene_sel)
            if sp.issparse(adata.X):
                gene_expr = np.array(adata.X[idx, col_idx]).flatten()
            else:
                gene_expr = adata.X[idx, col_idx]

    if gene_expr is not None:
        marker = dict(
            size=4,
            color=gene_expr,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title=gene_sel, tickfont=dict(color="#9aa7b8")),
        )
        hover = [f"{gene_sel}: {v:.2f}" for v in gene_expr]
    elif color_by and color_by in adata.obs.columns:
        cats = adata.obs[color_by].iloc[idx].astype(str).values
        unique_cats = list(dict.fromkeys(cats))
        palette = [
            "#4f7cff", "#39d98a", "#ffb020", "#ff5c7a", "#9b6cff",
            "#30d5c8", "#ff5c9c", "#ffd166", "#06d6a0", "#ef476f",
        ]
        cat_color = {c: palette[i % len(palette)] for i, c in enumerate(unique_cats)}
        colors = [cat_color[c] for c in cats]
        marker = dict(size=4, color=colors, opacity=0.8)
        hover = [f"{color_by}: {c}" for c in cats]
    else:
        marker = dict(size=3, color="#4f7cff", opacity=0.6)
        hover = [f"({xi:.1f}, {yi:.1f})" for xi, yi in zip(x, y)]

    fig = go.Figure(go.Scatter(
        x=x, y=y, mode="markers",
        marker=marker,
        text=hover, hoverinfo="text",
    ))
    fig.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,24,40,1)",
        font_color="#f4f7fb",
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis=dict(showgrid=False, zeroline=False, color="#9aa7b8", title="x (µm)"),
        yaxis=dict(showgrid=False, zeroline=False, color="#9aa7b8", title="y (µm)",
                   scaleanchor="x", scaleratio=1),
        showlegend=False,
    )
    st.plotly_chart(
        fig, use_container_width=True,
        config={"displayModeBar": False},
        key="spatial_preview_fig",
    )

    if n_total > max_points:
        st.caption(
            f"Showing {max_points:,} of {n_total:,} spots/cells for rendering performance."
        )


# ---------------------------------------------------------------------------
# Legacy alias
# ---------------------------------------------------------------------------

def data_readiness_score(adata: ad.AnnData) -> Tuple[int, str]:
    """Legacy function — returns (score, status)."""
    rd = adata.uns.get("mbsi_readiness") or compute_readiness(adata)
    return rd["score"], rd["status"]
