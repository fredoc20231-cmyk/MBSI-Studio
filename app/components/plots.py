"""
Plotting components for the UI.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, List

DARK_BG = "#07111f"
DARK_PANEL = "#0d1828"
DARK_FONT = "#f4f7fb"
DARK_GRID = "#22314a"


def _dark_layout(title: str = "", **kwargs) -> dict:
    layout = dict(
        title=title,
        paper_bgcolor=DARK_PANEL,
        plot_bgcolor=DARK_BG,
        font=dict(color=DARK_FONT, size=11),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(showgrid=True, gridcolor=DARK_GRID, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=DARK_GRID, zeroline=False),
    )
    layout.update(kwargs)
    return layout


def spatial_plot(
    coords,
    values,
    title: str = "Spatial Plot",
    color_scale: str = "Viridis",
    point_size: int = 10,
    opacity: float = 0.7,
    show_colorbar: bool = True
) -> go.Figure:
    """
    Create an interactive spatial scatter plot.
    
    Parameters
    ----------
    coords : ndarray
        Spatial coordinates (n x 2)
    values : ndarray
        Values for coloring (n,)
    title : str
        Plot title
    color_scale : str
        Plotly color scale name
    point_size : int
        Point size
    opacity : float
        Point opacity (0-1)
    show_colorbar : bool
        Whether to show colorbar
        
    Returns
    -------
    fig : go.Figure
        Plotly figure
    """
    fig = go.Figure(data=go.Scatter(
        x=coords[:, 0],
        y=coords[:, 1],
        mode='markers',
        marker=dict(
            size=point_size,
            color=values,
            colorscale=color_scale,
            showscale=show_colorbar,
            colorbar=dict(title="Expression"),
            opacity=opacity
        ),
        text=[f"Value: {v:.2f}" for v in values],
        hovertemplate='X: %{x:.2f}<br>Y: %{y:.2f}<br>%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        **_dark_layout(title, xaxis_title="X coordinate", yaxis_title="Y coordinate", hovermode='closest')
    )
    
    return fig


def donut_chart(composition: dict, title: str = "Cell Composition") -> go.Figure:
    """Donut chart for cell type composition."""
    labels = list(composition.keys())
    values = list(composition.values())
    colors = px.colors.qualitative.Set2[: len(labels)]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors), textinfo="percent", textfont_size=10,
    )])
    fig.update_layout(**_dark_layout(title), showlegend=True,
                      legend=dict(bgcolor=DARK_PANEL, bordercolor=DARK_GRID))
    return fig


def pseudotime_plot(coords, pseudotime, title: str = "Pseudotime") -> go.Figure:
    """Spatial pseudotime scatter."""
    fig = go.Figure(data=go.Scattergl(
        x=coords[:, 0], y=coords[:, 1], mode="markers",
        marker=dict(size=3, color=pseudotime, colorscale="Plasma", opacity=0.8,
                    colorbar=dict(title="PT", len=0.5)),
    ))
    fig.update_layout(**_dark_layout(title))
    fig.update_yaxes(autorange="reversed")
    return fig


def causal_bar_chart(drivers: list, title: str = "Causal Drivers") -> go.Figure:
    """Horizontal bar chart for causal driver ranking."""
    genes = [d["gene"] for d in drivers[:8]]
    scores = [d["score"] for d in drivers[:8]]
    fig = go.Figure(data=[go.Bar(
        y=genes, x=scores, orientation="h",
        marker=dict(color=scores, colorscale=[[0, "#4f7cff"], [1, "#ff5c7a"]]),
    )])
    fig.update_layout(**_dark_layout(title), yaxis=dict(autorange="reversed"))
    return fig


def invasion_heatmap(data, title: str = "Invasion Corridors") -> go.Figure:
    """Invasion / boundary leakage heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=data,
        colorscale=[[0, "#07111f"], [0.5, "#ffb020"], [1, "#ff5c7a"]],
        colorbar=dict(title="Score", len=0.5),
    ))
    fig.update_layout(**_dark_layout(title))
    return fig


def treatment_radar(radar: dict, title: str = "Treatment Response") -> go.Figure:
    """Radar chart comparing treatment scenarios."""
    categories = radar["categories"]
    fig = go.Figure()
    for name, values in radar.get("series", {}).items():
        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself", name=name, opacity=0.6,
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], gridcolor=DARK_GRID),
                   bgcolor=DARK_BG),
        **_dark_layout(title),
    )
    return fig


def marker_expression_bars(marker_maps: dict, gene: str, title: str = "") -> go.Figure:
    """Bar chart of marker expression distribution."""
    if gene not in marker_maps:
        fig = go.Figure()
        fig.update_layout(**_dark_layout(f"No data for {gene}"))
        return fig
    vals = marker_maps[gene]
    fig = go.Figure(data=[go.Histogram(x=vals, nbinsx=30, marker_color="#4f7cff", opacity=0.85)])
    fig.update_layout(**_dark_layout(title or f"{gene} Expression"))
    return fig


def violin_plot(
    data: pd.DataFrame,
    value_col: str,
    group_col: Optional[str] = None,
    title: str = "Violin Plot"
) -> go.Figure:
    """
    Create a violin plot.
    
    Parameters
    ----------
    data : DataFrame
        Data to plot
    value_col : str
        Column with values
    group_col : str, optional
        Column for grouping
    title : str
        Plot title
        
    Returns
    -------
    fig : go.Figure
        Plotly figure
    """
    if group_col:
        fig = px.violin(
            data,
            y=value_col,
            x=group_col,
            title=title,
            box=True
        )
    else:
        fig = px.violin(
            data,
            y=value_col,
            title=title,
            box=True
        )
    
    fig.update_layout(plot_bgcolor='white')
    return fig


def histogram_plot(
    values,
    title: str = "Histogram",
    bins: int = 50,
    color: str = "#667eea"
) -> go.Figure:
    """
    Create a histogram plot.
    
    Parameters
    ----------
    values : array-like
        Values to histogram
    title : str
        Plot title
    bins : int
        Number of bins
    color : str
        Bar color
        
    Returns
    -------
    fig : go.Figure
        Plotly figure
    """
    fig = go.Figure(data=[go.Histogram(
        x=values,
        nbinsx=bins,
        marker_color=color,
        opacity=0.7
    )])
    
    fig.update_layout(
        title=title,
        xaxis_title="Value",
        yaxis_title="Count",
        plot_bgcolor='white'
    )
    
    return fig


def scatter_plot(
    x,
    y,
    title: str = "Scatter Plot",
    x_label: str = "X",
    y_label: str = "Y",
    color: Optional[str] = None,
    add_diagonal: bool = True
) -> go.Figure:
    """
    Create a scatter plot.
    
    Parameters
    ----------
    x : array-like
        X values
    y : array-like
        Y values
    title : str
        Plot title
    x_label : str
        X axis label
    y_label : str
        Y axis label
    color : str, optional
        Point color
    add_diagonal : bool
        Whether to add diagonal line
        
    Returns
    -------
    fig : go.Figure
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='markers',
        marker=dict(color=color if color else "#667eea", size=6, opacity=0.6),
        name="Data"
    ))
    
    if add_diagonal:
        min_val = min(min(x), min(y))
        max_val = max(max(x), max(y))
        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            line=dict(color='red', dash='dash'),
            name='y=x'
        ))
    
    # Compute correlation
    from scipy.stats import pearsonr
    corr, _ = pearsonr(x, y)
    
    fig.update_layout(
        title=f"{title} (r={corr:.3f})",
        xaxis_title=x_label,
        yaxis_title=y_label,
        plot_bgcolor='white'
    )
    
    return fig


def radar_chart(
    categories: List[str],
    values: List[float],
    title: str = "Radar Chart"
) -> go.Figure:
    """
    Create a radar chart.
    
    Parameters
    ----------
    categories : list
        Category names
    values : list
        Values for each category
    title : str
        Plot title
        
    Returns
    -------
    fig : go.Figure
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Values'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(values) * 1.1]
            )
        ),
        title=title,
        showlegend=True
    )
    
    return fig


def heatmap_plot(
    data,
    title: str = "Heatmap",
    color_scale: str = "Viridis"
) -> go.Figure:
    """
    Create a heatmap plot.
    
    Parameters
    ----------
    data : 2D array
        Data to plot
    title : str
        Plot title
    color_scale : str
        Color scale name
        
    Returns
    -------
    fig : go.Figure
        Plotly figure
    """
    fig = go.Figure(data=go.Heatmap(
        z=data,
        colorscale=color_scale
    ))
    
    fig.update_layout(title=title)
    return fig


def bar_chart(
    categories: List[str],
    values: List[float],
    title: str = "Bar Chart",
    color: str = "#667eea",
    horizontal: bool = False
) -> go.Figure:
    """
    Create a bar chart.
    
    Parameters
    ----------
    categories : list
        Category names
    values : list
        Values for each category
    title : str
        Plot title
    color : str
        Bar color
    horizontal : bool
        Whether to make horizontal
        
    Returns
    -------
    fig : go.Figure
        Plotly figure
    """
    if horizontal:
        fig = go.Figure(data=[go.Bar(
            x=values,
            y=categories,
            orientation='h',
            marker_color=color
        )])
        fig.update_layout(yaxis_title="Category", xaxis_title="Value")
    else:
        fig = go.Figure(data=[go.Bar(
            x=categories,
            y=values,
            marker_color=color
        )])
        fig.update_layout(xaxis_title="Category", yaxis_title="Value")
    
    fig.update_layout(title=title, plot_bgcolor='white')
    return fig


def box_plot(
    data: pd.DataFrame,
    value_col: str,
    group_col: Optional[str] = None,
    title: str = "Box Plot"
) -> go.Figure:
    """
    Create a box plot.
    
    Parameters
    ----------
    data : DataFrame
        Data to plot
    value_col : str
        Column with values
    group_col : str, optional
        Column for grouping
    title : str
        Plot title
        
    Returns
    -------
    fig : go.Figure
        Plotly figure
    """
    if group_col:
        fig = px.box(data, y=value_col, x=group_col, title=title)
    else:
        fig = px.box(data, y=value_col, title=title)
    
    fig.update_layout(plot_bgcolor='white')
    return fig
