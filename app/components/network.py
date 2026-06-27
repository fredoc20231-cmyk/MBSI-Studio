"""Network graph visualizations."""

import plotly.graph_objects as go
import pandas as pd

DARK = dict(
    paper_bgcolor="#0d1828",
    plot_bgcolor="#07111f",
    font=dict(color="#f4f7fb", size=10),
    margin=dict(l=10, r=10, t=30, b=10),
)


def neighborhood_graph(nodes: pd.DataFrame, edges: pd.DataFrame, title: str = "Cell Neighborhood") -> go.Figure:
    fig = go.Figure()
    for ct, sub in nodes.groupby("cell_type"):
        fig.add_trace(go.Scatter(
            x=sub["x"], y=sub["y"], mode="markers+text",
            marker=dict(size=12, color=sub["color"].iloc[0]),
            text=[""] * len(sub), name=ct,
        ))
    edge_x, edge_y = [], []
    for _, e in edges.iterrows():
        s = nodes[nodes["id"] == e["source"]].iloc[0]
        t = nodes[nodes["id"] == e["target"]].iloc[0]
        edge_x += [s["x"], t["x"], None]
        edge_y += [s["y"], t["y"], None]
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(color="#22314a", width=1), hoverinfo="skip", showlegend=False,
    ))
    fig.update_layout(title=title, **DARK,
                      xaxis=dict(showgrid=False, zeroline=False, visible=False),
                      yaxis=dict(showgrid=False, zeroline=False, visible=False),
                      legend=dict(font=dict(size=8), bgcolor="#0d1828"))
    return fig


def interactions_bar(interactions: pd.DataFrame, title: str = "Top Interactions (Niche → Target)") -> go.Figure:
    labels = [f"{r.niche} → {r.target}" for r in interactions.itertuples()]
    fig = go.Figure(data=[go.Bar(
        y=labels, x=interactions["score"], orientation="h",
        marker=dict(color=interactions["score"], colorscale=[[0, "#4f7cff"], [1, "#39d98a"]]),
    )])
    fig.update_layout(
        title=title, **DARK,
        xaxis=dict(title="Communication Probability", range=[0, 1], gridcolor="#22314a"),
        yaxis=dict(autorange="reversed"),
        height=220,
    )
    return fig
