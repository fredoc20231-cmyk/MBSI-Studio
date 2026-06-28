"""Plotly visualizations for communication intelligence."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DARK = {
    "paper_bgcolor": "#0d1828",
    "plot_bgcolor": "#07111f",
    "font": {"color": "#f4f7fb", "size": 10},
}


def _layout(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    fig.update_layout(title=title, **DARK, height=height, margin=dict(l=40, r=20, t=40, b=40))
    return fig


def plot_signaling_map(niche_map: dict, title: str = "Spatial Signaling Flux") -> go.Figure:
    fig = px.scatter(
        x=niche_map["x"], y=niche_map["y"], color=niche_map["flux"],
        color_continuous_scale="Inferno",
        labels={"color": "flux"},
    )
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, title)


def plot_pathway_rankings(rankings: pd.DataFrame) -> go.Figure:
    df = rankings.head(10)
    fig = go.Figure(data=go.Bar(x=df["score"], y=df.get("pathway_name", df["pathway"]), orientation="h"))
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _layout(fig, "Pathway Rankings (computational hypothesis)")


def plot_sender_receiver_network(edges: pd.DataFrame, max_edges: int = 40) -> Optional[go.Figure]:
    if edges is None or edges.empty:
        return None
    df = edges.nlargest(max_edges, "flux")
    fig = go.Figure(data=go.Scatter(
        x=df["flux"], y=df["receiver"], mode="markers",
        marker=dict(size=8, color=df["flux"], colorscale="Viridis"),
        text=df["sender"],
    ))
    return _layout(fig, "Sender → Receiver Flux (top edges)")
