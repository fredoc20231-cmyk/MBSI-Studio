"""Neighborhood graph visualization."""

from typing import Optional

import networkx as nx
import numpy as np
import plotly.graph_objects as go


def neighborhood_graph_figure(
    graph: nx.Graph,
    coords: Optional[np.ndarray] = None,
    max_nodes: int = 400,
    title: str = "Neighborhood Graph",
) -> go.Figure:
    """Render k-NN neighborhood graph with spatial layout."""
    nodes = list(graph.nodes())
    if len(nodes) > max_nodes:
        nodes = nodes[:max_nodes]
        sub = graph.subgraph(nodes)
    else:
        sub = graph

    if coords is not None and len(coords) > 0:
        pos = {}
        for n in sub.nodes():
            idx = int(n) if int(n) < len(coords) else int(n) % len(coords)
            pos[n] = (float(coords[idx, 0]), float(coords[idx, 1]))
    else:
        pos = nx.spring_layout(sub, seed=42, k=0.5)

    edge_x, edge_y = [], []
    for u, v in sub.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x = [pos[n][0] for n in sub.nodes()]
    node_y = [pos[n][1] for n in sub.nodes()]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.5, color="#22314a"),
        hoverinfo="none", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers",
        marker=dict(size=5, color="#4f7cff", opacity=0.8, line=dict(width=0.5, color="#07111f")),
        hoverinfo="text",
        text=[f"Cell {n}" for n in sub.nodes()],
        name="Cells",
    ))
    fig.update_layout(
        title=title,
        paper_bgcolor="#0d1828", plot_bgcolor="#07111f",
        font=dict(color="#f4f7fb", size=10),
        margin=dict(l=5, r=5, t=30, b=5),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        showlegend=False,
    )
    return fig
