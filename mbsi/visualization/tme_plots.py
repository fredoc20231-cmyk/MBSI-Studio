"""Plotly visualizations for TME intelligence."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go

DARK = {
    "paper_bgcolor": "#0d1828",
    "plot_bgcolor": "#07111f",
    "font": {"color": "#f4f7fb", "size": 10},
}


def plot_niche_map(x, y, score, title: str = "TME Niche Map") -> go.Figure:
    fig = px.scatter(x=x, y=y, color=score, color_continuous_scale="Inferno", labels={"color": "score"})
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title=title, **DARK, height=380, margin=dict(l=40, r=20, t=40, b=40))
    return fig


def plot_niche_summary(summary_df) -> go.Figure:
    fig = go.Figure(data=go.Bar(
        x=summary_df["niche_type"],
        y=summary_df["mean_score"],
        marker_color="#4f7cff",
    ))
    fig.update_layout(
        title="TME Niche Scores (computational hypothesis)",
        **DARK,
        height=360,
        margin=dict(l=40, r=20, t=40, b=80),
    )
    return fig
