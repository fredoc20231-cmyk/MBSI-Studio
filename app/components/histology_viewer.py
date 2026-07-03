"""Real histology extraction and overlay — no synthetic fallback in production paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app.components.developer_mode import is_developer_mode

PLOT_THEME = {
    "paper_bgcolor": "#0d1828",
    "plot_bgcolor": "#07111f",
    "font": {"color": "#f4f7fb", "size": 10},
    "margin": {"l": 4, "r": 4, "t": 32, "b": 4},
}


def _resolve_spatial_library(spatial_uns: dict) -> Tuple[Optional[str], Optional[dict]]:
    if not spatial_uns or not isinstance(spatial_uns, dict):
        return None, None
    library_id = spatial_uns.get("library_id")
    if library_id and library_id != "library_id" and isinstance(spatial_uns.get(library_id), dict):
        return str(library_id), spatial_uns[library_id]
    for key, val in spatial_uns.items():
        if key == "library_id":
            continue
        if isinstance(val, dict) and "images" in val:
            return str(key), val
    return None, None


def _load_image_file(path: Union[str, Path]) -> Optional[np.ndarray]:
    path = Path(path)
    if not path.exists():
        return None
    try:
        from PIL import Image

        img = Image.open(path)
        if getattr(img, "n_frames", 1) > 1:
            img.seek(0)
        arr = np.asarray(img.convert("RGB"))
        return arr
    except Exception:
        try:
            import tifffile

            arr = tifffile.imread(path)
            if arr.ndim == 2:
                arr = np.stack([arr, arr, arr], axis=-1)
            elif arr.ndim == 3 and arr.shape[-1] not in (3, 4):
                arr = arr[0]
            if arr.shape[-1] == 4:
                arr = arr[..., :3]
            return np.asarray(arr)
        except Exception:
            return None


def extract_histology_from_adata(adata) -> Tuple[Optional[np.ndarray], Optional[str], Optional[str]]:
    """
    Extract tissue image from AnnData.

    Returns (image_array, image_source_label, library_id).
    """
    if adata is None:
        return None, None, None

    spatial_uns = adata.uns.get("spatial")
    if spatial_uns:
        library_id, lib_data = _resolve_spatial_library(spatial_uns)
        if lib_data:
            images = lib_data.get("images") or {}
            for res_key, label in (("hires", "Visium hires image"), ("lowres", "Visium lowres image")):
                if res_key in images and images[res_key] is not None:
                    img = np.asarray(images[res_key])
                    if img.size:
                        return img, label, library_id

    xenium_uns = adata.uns.get("xenium") or {}
    artifacts = xenium_uns.get("optional_artifacts") or {}
    morph_path = artifacts.get("morphology")
    if morph_path:
        img = _load_image_file(morph_path)
        if img is not None and img.size:
            return img, "Xenium morphology image", "xenium"

    return None, None, None


def get_visium_coord_scale(adata, image_source: Optional[str]) -> float:
    """Scale obsm spatial coords to match displayed Visium image resolution."""
    if adata is None or "spatial" not in adata.uns:
        return 1.0
    _, lib_data = _resolve_spatial_library(adata.uns["spatial"])
    if not lib_data:
        return 1.0
    sf = lib_data.get("scalefactors") or {}
    if image_source and "lowres" in image_source.lower():
        return float(sf.get("tissue_lowres_scalef", 1.0))
    return float(sf.get("tissue_hires_scalef", 1.0))


def get_active_histology_image(adata=None) -> Tuple[Optional[np.ndarray], str]:
    """
    Resolve histology for the active session.

    Returns (image_or_none, source_description).
    """
    if st.session_state.get("using_synthetic_demo") and not is_developer_mode():
        return None, "No histology image detected"
    if st.session_state.get("using_synthetic_demo"):
        return None, "Developer demo mode — synthetic data only"

    uploaded = st.session_state.get("uploaded_image")
    if uploaded is not None:
        arr = np.asarray(uploaded)
        if arr.size:
            return arr, "Uploaded image"

    ad = adata if adata is not None else st.session_state.get("adata")
    img, source, _ = extract_histology_from_adata(ad)
    if img is not None:
        return img, source or "AnnData spatial image"

    if ad is not None:
        xenium_uns = (ad.uns or {}).get("xenium") or {}
        if xenium_uns and "morphology" not in (xenium_uns.get("optional_artifacts") or {}):
            platform = st.session_state.get("mbsi_platform") or st.session_state.get("selected_technology", "")
            if platform == "xenium":
                return None, "Xenium morphology image not found in uploaded bundle"

    return None, "No histology image detected"


def sync_histology_session_from_adata(adata=None) -> None:
    """Populate uploaded_image from adata.uns when no explicit upload exists."""
    if adata is None:
        adata = st.session_state.get("adata")
    if adata is None:
        return
    if st.session_state.get("uploaded_image") is not None:
        return
    img, source, _ = extract_histology_from_adata(adata)
    if img is not None:
        st.session_state.uploaded_image = img
        st.session_state.histology_source = source


def _color_values(adata, color_by: Optional[str]) -> Tuple[Optional[np.ndarray], Optional[str], bool]:
    if adata is None or color_by is None:
        return None, None, False
    if color_by in adata.obs.columns:
        series = adata.obs[color_by]
        if series.dtype.kind in ("i", "u", "f"):
            return np.asarray(series, dtype=float), color_by, False
        return series.astype(str).values, color_by, True
    if color_by in adata.var_names:
        x = adata[:, color_by].X
        if hasattr(x, "toarray"):
            x = x.toarray()
        return np.asarray(x).ravel().astype(float), color_by, False
    return None, None, False


def render_histology_overlay(
    adata=None,
    image: Optional[np.ndarray] = None,
    coords: Optional[np.ndarray] = None,
    color: Optional[str] = "total_counts",
    title: str = "Histology overlay",
    *,
    show_image: bool = True,
    show_spots: bool = True,
    opacity: float = 0.85,
    point_size: float = 4.0,
    image_source: Optional[str] = None,
    return_figure: bool = False,
):
    """
    Render histology with spatial coordinate overlay.

    If return_figure=True, returns Plotly Figure; otherwise displays via st.plotly_chart.
    """
    ad = adata if adata is not None else st.session_state.get("adata")
    if image is None:
        image, resolved_source = get_active_histology_image(ad)
        image_source = image_source or resolved_source
    elif image_source is None:
        image_source = "Provided image"

    if coords is None and ad is not None and "spatial" in ad.obsm:
        coords = np.asarray(ad.obsm["spatial"], dtype=float)
        if image is not None and image_source and "visium" in image_source.lower():
            scale = get_visium_coord_scale(ad, image_source)
            if scale and scale != 1.0:
                coords = coords * scale

    fig = go.Figure()
    img_h, img_w = (0, 0)
    if show_image and image is not None:
        img = np.asarray(image)
        if img.ndim == 2:
            img = np.stack([img, img, img], axis=-1)
        img_h, img_w = img.shape[:2]
        fig.add_trace(
            go.Image(
                z=img,
                x0=0,
                y0=0,
                dx=1,
                dy=1,
                hoverinfo="skip",
                name="Histology",
            )
        )

    if show_spots and coords is not None and len(coords):
        color_vals, color_label, is_categorical = _color_values(ad, color)
        marker: Dict[str, Any] = {"size": point_size, "opacity": opacity}
        if color_vals is not None and not is_categorical:
            marker.update(
                color=color_vals,
                colorscale=[[0, "#1e3a8a"], [0.5, "#fbbf24"], [1, "#f87171"]],
                showscale=True,
                colorbar=dict(title=color_label or color, len=0.5),
            )
        elif color_vals is not None:
            marker.update(color=color_vals)
        else:
            marker.update(color="#4f7cff")

        fig.add_trace(
            go.Scattergl(
                x=coords[:, 0],
                y=coords[:, 1],
                mode="markers",
                marker=marker,
                name=color_label or "spots",
                showlegend=False,
            )
        )

    layout = dict(PLOT_THEME)
    layout["title"] = dict(text=title, font=dict(size=12))
    fig.update_layout(**layout)
    fig.update_layout(
        xaxis=dict(visible=False, range=[0, max(img_w, 1)] if img_w else None),
        yaxis=dict(visible=False, scaleanchor="x", autorange="reversed"),
        showlegend=False,
    )

    if return_figure:
        return fig
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    return fig


def histology_status_caption(adata=None) -> str:
    """Human-readable histology source line for UI captions."""
    _, source = get_active_histology_image(adata)
    if source.startswith("No ") or source.startswith("Xenium morphology"):
        return f"**Histology source:** {source}"
    return f"**Histology source:** {source}"


def color_by_options(adata) -> List[str]:
    """Build color-by choices for visualization controls."""
    if adata is None:
        return ["total_counts"]
    opts: List[str] = []
    for col in ("total_counts", "n_genes_by_counts", "cluster", "leiden", "cell_type", "domain"):
        if col in adata.obs.columns:
            opts.append(col)
    opts.extend(list(adata.var_names[:50]))
    return opts or ["total_counts"]
