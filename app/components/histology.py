"""Histology overlay visualization."""

from typing import Dict, List, Optional

import numpy as np
import plotly.graph_objects as go

PLOT_THEME = {
    "paper_bgcolor": "#0d1828",
    "plot_bgcolor": "#07111f",
    "font": {"color": "#f4f7fb", "size": 10},
}


def _apply_dark_layout(fig: go.Figure, *, title: str = "", height: Optional[int] = None, margin=None) -> go.Figure:
    layout_kwargs = dict(PLOT_THEME)
    if title:
        layout_kwargs["title"] = dict(text=title, font=dict(size=12))
    if height is not None:
        layout_kwargs["height"] = height
    if margin is not None:
        layout_kwargs["margin"] = margin
    else:
        layout_kwargs["margin"] = dict(l=4, r=4, t=28, b=4)
    fig.update_layout(**layout_kwargs)
    return fig


def make_histology_overlay(
    histology: np.ndarray,
    cells_df,
    tissue_extent: float = 1000.0,
    show_he: bool = True,
    show_cells: bool = True,
    show_boundaries: bool = True,
    show_types: bool = True,
    selected_types: Optional[List[str]] = None,
    boundaries: Optional[List[Dict]] = None,
    title: str = "Histology & Reconstruction Overlay",
) -> go.Figure:
    """Build reference-style histology + cell overlay figure."""
    fig = go.Figure()
    h, w = histology.shape[:2]

    if show_he:
        fig.add_trace(
            go.Image(
                z=histology,
                x0=0,
                y0=0,
                dx=tissue_extent / w,
                dy=tissue_extent / h,
                hoverinfo="skip",
                name="H&E",
            )
        )

    if show_cells and cells_df is not None and len(cells_df):
        df = cells_df.copy()
        if selected_types:
            df = df[df["cell_type"].isin(selected_types)]
        if show_types:
            for ct, sub in df.groupby("cell_type"):
                color = sub["color"].iloc[0] if "color" in sub.columns else "#4f7cff"
                fig.add_trace(
                    go.Scattergl(
                        x=sub["x"],
                        y=sub["y"],
                        mode="markers",
                        marker=dict(size=2.5, color=color, opacity=0.85),
                        name=ct,
                        showlegend=False,
                    )
                )
        else:
            fig.add_trace(
                go.Scattergl(
                    x=df["x"],
                    y=df["y"],
                    mode="markers",
                    marker=dict(size=2.5, color="#4f7cff", opacity=0.7),
                    showlegend=False,
                )
            )

    if show_boundaries and boundaries:
        for b in boundaries:
            color = b.get("color", "#f7c948")
            if "x" in b and "y" in b:
                bx = [v * tissue_extent for v in b["x"]]
                by = [v * tissue_extent for v in b["y"]]
                if bx and by:
                    fig.add_trace(
                        go.Scattergl(
                            x=bx + [bx[0]],
                            y=by + [by[0]],
                            mode="lines",
                            line=dict(color=color, width=2),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                    )
            elif "x0" in b:
                fig.add_shape(
                    type="rect",
                    x0=b["x0"] * tissue_extent,
                    y0=b["y0"] * tissue_extent,
                    x1=b["x1"] * tissue_extent,
                    y1=b["y1"] * tissue_extent,
                    line=dict(color=color, width=2),
                )

    sb_len = 250
    fig.add_shape(
        type="line",
        x0=tissue_extent * 0.04,
        y0=tissue_extent * 0.96,
        x1=tissue_extent * 0.04 + sb_len,
        y1=tissue_extent * 0.96,
        line=dict(color="#f4f7fb", width=3),
    )
    fig.add_annotation(
        x=tissue_extent * 0.04 + sb_len / 2,
        y=tissue_extent * 0.985,
        text="250 µm",
        showarrow=False,
        font=dict(size=9, color="#9aa7b8"),
    )

    _apply_dark_layout(fig, title=title)
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x"), showlegend=False)
    fig.update_yaxes(autorange="reversed")
    return fig


def make_marker_spatial_heatmap(field: np.ndarray, title: str = "Marker") -> go.Figure:
    fig = go.Figure(
        data=go.Heatmap(
            z=field,
            colorscale=[[0, "#07111f"], [0.5, "#ffb020"], [1, "#ff5c7a"]],
            showscale=False,
        )
    )
    _apply_dark_layout(fig, title=title)
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def make_ligand_gradient(field: np.ndarray, title: str = "Ligand Gradient (CXCL12)") -> go.Figure:
    fig = go.Figure(
        data=go.Heatmap(
            z=field,
            colorscale=[[0, "#1e3a8a"], [0.5, "#30d5c8"], [1, "#ff5c7a"]],
            colorbar=dict(title="", len=0.4, tickfont=dict(size=8)),
        )
    )
    _apply_dark_layout(fig, title=title, margin=dict(l=4, r=4, t=24, b=4))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig
