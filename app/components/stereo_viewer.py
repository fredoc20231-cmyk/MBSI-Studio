"""Plotly-based interactive viewer for STOmics Stereo-seq multi-scale spatial data."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import anndata as ad
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.components.theme import apply_plotly_theme


def _coords(adata: ad.AnnData) -> np.ndarray:
    if "spatial" in adata.obsm:
        return np.asarray(adata.obsm["spatial"])
    if "x" in adata.obs and "y" in adata.obs:
        return adata.obs[["x", "y"]].values
    raise ValueError("AnnData missing spatial coordinates")


def _color_values(adata: ad.AnnData, color_by: Optional[str], gene: Optional[str]) -> np.ndarray:
    if gene and gene in adata.var_names:
        x = adata[:, gene].X
        return np.asarray(x).flatten() if not hasattr(x, "toarray") else x.toarray().flatten()
    if color_by and color_by in adata.obs.columns:
        vals = adata.obs[color_by]
        if vals.dtype.kind in ("i", "u", "f"):
            return vals.values.astype(float)
        codes, _ = np.unique(vals.astype(str), return_inverse=True)
        return codes.astype(float)
    if "total_counts" in adata.obs:
        return adata.obs["total_counts"].values.astype(float)
    return np.zeros(adata.n_obs)


def build_stereo_viewer_figure(
    adata: ad.AnnData,
    *,
    color_by: Optional[str] = None,
    gene: Optional[str] = None,
    show_bins: bool = True,
    show_cells: bool = False,
    show_regions: bool = False,
    show_communication: bool = False,
    communication_scores: Optional[Dict[str, float]] = None,
    title: str = "Stereo-seq spatial viewer",
) -> go.Figure:
    """Build multi-layer Plotly figure with bin/cell/region overlays."""
    coords = _coords(adata)
    colors = _color_values(adata, color_by, gene)
    scale = adata.obs.get("stereo_scale", "bin")
    marker_size = 3 if str(scale.iloc[0] if hasattr(scale, "iloc") else scale) == "bin" else 6

    fig = go.Figure()
    if show_bins:
        fig.add_trace(
            go.Scattergl(
                x=coords[:, 0],
                y=coords[:, 1],
                mode="markers",
                marker=dict(size=marker_size, color=colors, colorscale="Viridis", showscale=True, opacity=0.85),
                name="Bins" if show_cells is False else "Bins (base)",
                hovertemplate="x=%{x:.1f}<br>y=%{y:.1f}<extra></extra>",
            )
        )

    if show_cells and "cell_id" in adata.obs:
        cell_mask = adata.obs["cell_id"].notna()
        fig.add_trace(
            go.Scattergl(
                x=coords[cell_mask, 0],
                y=coords[cell_mask, 1],
                mode="markers",
                marker=dict(size=8, color="rgba(255,120,80,0.6)", line=dict(width=0.5, color="white")),
                name="Cells",
            )
        )

    if show_regions and "region_id" in adata.obs:
        regions = adata.obs["region_id"].astype(str)
        uniq = sorted(regions.unique())
        for i, rid in enumerate(uniq[:12]):
            m = regions == rid
            fig.add_trace(
                go.Scattergl(
                    x=coords[m, 0],
                    y=coords[m, 1],
                    mode="markers",
                    marker=dict(size=4, opacity=0.5),
                    name=f"Region {rid}",
                    visible="legendonly" if i > 3 else True,
                )
            )

    if show_communication and communication_scores:
        top_genes = sorted(communication_scores, key=communication_scores.get, reverse=True)[:5]
        for g in top_genes:
            if g in adata.var_names:
                expr = adata[:, g].X
                expr = np.asarray(expr).flatten() if not hasattr(expr, "toarray") else expr.toarray().flatten()
                fig.add_trace(
                    go.Scattergl(
                        x=coords[:, 0],
                        y=coords[:, 1],
                        mode="markers",
                        marker=dict(size=5, color=expr, colorscale="Reds", showscale=False, opacity=0.4),
                        name=f"L-R: {g}",
                        visible="legendonly",
                    )
                )

    fig.update_yaxes(autorange="reversed", scaleanchor="x", scaleratio=1)
    fig.update_xaxes(constrain="domain")
    fig.update_layout(
        title=title,
        dragmode="zoom",
        hovermode="closest",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return apply_plotly_theme(fig)


def render_stereo_viewer(
    adata: ad.AnnData,
    *,
    module: str = "spatial_analysis",
    key_prefix: str = "stereo_viewer",
) -> Optional[go.Figure]:
    """Streamlit-friendly wrapper — returns figure for render_interactive_plot."""
    import streamlit as st

    if adata is None or adata.n_obs == 0:
        st.info("Load Stereo-seq data to use the multi-scale viewer.")
        return None

    st.caption("Multi-scale Stereo-seq viewer — toggle overlays and zoom with scroll.")
    c1, c2, c3, c4 = st.columns(4)
    show_bins = c1.checkbox("Bins", value=True, key=f"{key_prefix}_bins")
    show_cells = c2.checkbox("Cells", value="cell_id" in adata.obs, key=f"{key_prefix}_cells")
    show_regions = c3.checkbox("Regions", value="region_id" in adata.obs, key=f"{key_prefix}_regions")
    show_comm = c4.checkbox("Communication", value=False, key=f"{key_prefix}_comm")

    color_opts = [c for c in ("cluster", "cell_type", "region_id", "total_counts") if c in adata.obs.columns]
    gene = None
    color_by = st.selectbox("Color by", color_opts or ["total_counts"], key=f"{key_prefix}_color")
    if not color_opts:
        color_by = "total_counts"

    genes = list(adata.var_names[: min(200, adata.n_vars)])
    if genes:
        gene_pick = st.selectbox("Marker gene overlay (optional)", ["—"] + genes, key=f"{key_prefix}_gene")
        if gene_pick != "—":
            gene = gene_pick

    comm_scores = st.session_state.get("communication_results", {}).get("ligand_scores")
    fig = build_stereo_viewer_figure(
        adata,
        color_by=color_by,
        gene=gene,
        show_bins=show_bins,
        show_cells=show_cells,
        show_regions=show_regions,
        show_communication=show_comm,
        communication_scores=comm_scores if isinstance(comm_scores, dict) else None,
        title=f"Stereo-seq — {adata.n_obs:,} observations",
    )
    return fig
