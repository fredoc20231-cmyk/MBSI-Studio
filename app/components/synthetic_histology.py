"""Synthetic H&E histology overlay with cell scatter."""

from typing import Dict, List, Optional

import numpy as np
import plotly.graph_objects as go
import streamlit as st

DARK_LAYOUT = dict(
    paper_bgcolor="#0d1828",
    plot_bgcolor="#07111f",
    font=dict(color="#f4f7fb", size=11),
    margin=dict(l=10, r=10, t=36, b=10),
    xaxis=dict(showgrid=False, zeroline=False, visible=False),
    yaxis=dict(showgrid=False, zeroline=False, visible=False, scaleanchor="x"),
)


def render_spatial_map(
    histology: np.ndarray,
    cells_df,
    cell_types: List[Dict],
    show_histology: bool = True,
    show_cells: bool = True,
    show_boundaries: bool = False,
    selected_types: Optional[List[str]] = None,
    marker_gene: Optional[str] = None,
    marker_values: Optional[np.ndarray] = None,
    tissue_extent: float = 1000.0,
    title: str = "Spatial Map",
) -> go.Figure:
    """Build histology + cell overlay figure."""
    fig = go.Figure()

    if show_histology and histology is not None:
        h, w = histology.shape[:2]
        fig.add_trace(go.Image(
            z=histology,
            x0=0,
            y0=0,
            dx=tissue_extent / w,
            dy=tissue_extent / h,
            hoverinfo="skip",
            name="H&E",
        ))

    if show_cells and cells_df is not None and len(cells_df):
        df = cells_df.copy()
        if selected_types:
            df = df[df["cell_type"].isin(selected_types)]

        color_map = {ct["name"]: ct["color"] for ct in cell_types}
        if marker_gene and marker_values is not None:
            fig.add_trace(go.Scattergl(
                x=df["x"], y=df["y"],
                mode="markers",
                marker=dict(
                    size=4,
                    color=marker_values[: len(df)],
                    colorscale="Viridis",
                    opacity=0.85,
                    colorbar=dict(title=marker_gene, len=0.5, y=0.75),
                ),
                name=marker_gene,
                hovertemplate="%{text}<extra></extra>",
                text=[f"{r.cell_type}" for r in df.itertuples()],
            ))
        else:
            for ct in cell_types:
                sub = df[df["cell_type"] == ct["name"]]
                if sub.empty:
                    continue
                fig.add_trace(go.Scattergl(
                    x=sub["x"], y=sub["y"],
                    mode="markers",
                    marker=dict(size=3, color=ct["color"], opacity=0.75),
                    name=ct["name"],
                    hovertemplate=f"{ct['name']}<extra></extra>",
                ))

    if show_boundaries:
        fig.add_shape(
            type="rect", x0=tissue_extent * 0.35, y0=tissue_extent * 0.30,
            x1=tissue_extent * 0.62, y1=tissue_extent * 0.58,
            line=dict(color="#ffb020", width=2, dash="dash"),
        )

    # Scale bar
    fig.add_annotation(
        x=tissue_extent * 0.08, y=tissue_extent * 0.95,
        text="200 µm", showarrow=False,
        font=dict(color="#9aa7b8", size=10),
    )
    fig.add_shape(
        type="line", x0=tissue_extent * 0.05, y0=tissue_extent * 0.93,
        x1=tissue_extent * 0.05 + 200, y1=tissue_extent * 0.93,
        line=dict(color="#f4f7fb", width=3),
    )

    fig.update_layout(title=title, **DARK_LAYOUT, showlegend=True,
                      legend=dict(bgcolor="#0d1828", bordercolor="#22314a", font=dict(size=9)))
    fig.update_yaxes(autorange="reversed")
    return fig


def render_legend(cell_types: List[Dict]) -> None:
    """HTML legend for cell types."""
    items = "".join(
        f'<span style="margin-right:12px;font-size:0.78rem;">'
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{ct["color"]};margin-right:4px;"></span>{ct["name"]}</span>'
        for ct in cell_types
    )
    st.markdown(f'<div class="mbsi-panel" style="padding:8px 12px;">{items}</div>', unsafe_allow_html=True)
