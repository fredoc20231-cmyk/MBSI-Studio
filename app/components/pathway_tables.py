"""Ligand-receptor pathway tables and heatmaps."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_lr_table(lr_df: pd.DataFrame, max_rows: int = 8) -> None:
    """Styled L-R pathway table."""
    if lr_df is None or lr_df.empty:
        st.info("No L-R pathways available.")
        return
    display = lr_df.head(max_rows).copy()
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "lr_score": st.column_config.ProgressColumn("LR Score", min_value=0, max_value=3),
            "flux": st.column_config.NumberColumn("Flux", format="%.3f"),
        },
    )


def ligand_gradient_heatmap(field: np.ndarray, title: str = "Ligand Gradient") -> go.Figure:
    """2D ligand diffusion field heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=field,
        colorscale=[
            [0, "#07111f"], [0.3, "#1a3a6b"], [0.6, "#4f7cff"], [1.0, "#39d98a"],
        ],
        colorbar=dict(title="Conc.", len=0.5, y=0.75),
    ))
    fig.update_layout(
        title=title,
        paper_bgcolor="#0d1828", plot_bgcolor="#07111f",
        font=dict(color="#f4f7fb", size=10),
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(showgrid=False, title="X"),
        yaxis=dict(showgrid=False, title="Y", autorange="reversed"),
    )
    return fig
