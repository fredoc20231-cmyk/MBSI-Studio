"""
Spatial expression visualization.

Creates spatial plots for gene expression, reconstruction comparisons,
and tissue structure visualization.
"""

from typing import Optional, List

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns


def plot_spatial_gene(
    adata: ad.AnnData,
    gene: str,
    title: Optional[str] = None,
    cmap: str = "viridis",
    spot_size: float = 100,
    figsize: tuple = (8, 6),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Plot spatial expression of a single gene.
    
    Parameters
    ----------
    adata : AnnData
        AnnData with spatial coordinates in obsm['spatial']
    gene : str
        Gene name to plot
    title : str, optional
        Plot title
    cmap : str
        Colormap
    spot_size : float
        Size of spots/cells
    figsize : tuple
        Figure size
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    if gene not in adata.var_names:
        raise ValueError(f"Gene {gene} not found in AnnData")
    
    coords = adata.obsm['spatial']
    expr = adata[:, gene].X
    
    if hasattr(expr, 'toarray'):
        expr = expr.toarray().flatten()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    scatter = ax.scatter(
        coords[:, 0],
        coords[:, 1],
        c=expr,
        s=spot_size,
        cmap=cmap,
        alpha=0.8
    )
    
    plt.colorbar(scatter, ax=ax, label=f"{gene} expression")
    
    if title is None:
        title = f"Spatial expression: {gene}"
    ax.set_title(title)
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None


def plot_reconstruction_scatter(
    true_adata: ad.AnnData,
    reconstructed_adata: ad.AnnData,
    gene: str,
    title: Optional[str] = None,
    figsize: tuple = (6, 6),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Scatter plot comparing true vs reconstructed expression.
    
    Parameters
    ----------
    true_adata : AnnData
        Ground truth AnnData
    reconstructed_adata : AnnData
        Reconstructed AnnData
    gene : str
        Gene name to compare
    title : str, optional
        Plot title
    figsize : tuple
        Figure size
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    if gene not in true_adata.var_names or gene not in reconstructed_adata.var_names:
        raise ValueError(f"Gene {gene} not found in both AnnData objects")
    
    true_expr = true_adata[:, gene].X
    recon_expr = reconstructed_adata[:, gene].X
    
    if hasattr(true_expr, 'toarray'):
        true_expr = true_expr.toarray().flatten()
    if hasattr(recon_expr, 'toarray'):
        recon_expr = recon_expr.toarray().flatten()
    
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.scatter(true_expr, recon_expr, alpha=0.5, s=20)
    
    # Add diagonal line
    max_val = max(true_expr.max(), recon_expr.max())
    ax.plot([0, max_val], [0, max_val], 'r--', label='y=x')
    
    # Compute correlation
    from scipy.stats import pearsonr
    corr, _ = pearsonr(true_expr, recon_expr)
    
    ax.set_xlabel("True expression")
    ax.set_ylabel("Reconstructed expression")
    
    if title is None:
        title = f"Reconstruction: {gene} (r={corr:.3f})"
    ax.set_title(title)
    ax.legend()
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None


def plot_spatial_comparison(
    true_adata: ad.AnnData,
    reconstructed_adata: ad.AnnData,
    gene: str,
    spot_size: float = 100,
    figsize: tuple = (16, 6),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Side-by-side spatial comparison of true vs reconstructed.
    
    Parameters
    ----------
    true_adata : AnnData
        Ground truth AnnData
    reconstructed_adata : AnnData
        Reconstructed AnnData
    gene : str
        Gene name
    spot_size : float
        Spot size
    figsize : tuple
        Figure size
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # True expression
    coords_true = true_adata.obsm['spatial']
    expr_true = true_adata[:, gene].X
    if hasattr(expr_true, 'toarray'):
        expr_true = expr_true.toarray().flatten()
    
    scatter1 = axes[0].scatter(
        coords_true[:, 0],
        coords_true[:, 1],
        c=expr_true,
        s=spot_size,
        cmap='viridis',
        alpha=0.8
    )
    plt.colorbar(scatter1, ax=axes[0])
    axes[0].set_title(f"True: {gene}")
    axes[0].set_xlabel("X")
    axes[0].set_ylabel("Y")
    
    # Reconstructed expression
    coords_recon = reconstructed_adata.obsm['spatial']
    expr_recon = reconstructed_adata[:, gene].X
    if hasattr(expr_recon, 'toarray'):
        expr_recon = expr_recon.toarray().flatten()
    
    scatter2 = axes[1].scatter(
        coords_recon[:, 0],
        coords_recon[:, 1],
        c=expr_recon,
        s=spot_size,
        cmap='viridis',
        alpha=0.8
    )
    plt.colorbar(scatter2, ax=axes[1])
    axes[1].set_title(f"Reconstructed: {gene}")
    axes[1].set_xlabel("X")
    axes[1].set_ylabel("Y")
    
    plt.tight_layout()
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None


def plot_multiple_genes(
    adata: ad.AnnData,
    genes: List[str],
    ncols: int = 4,
    spot_size: float = 50,
    figsize: Optional[tuple] = None,
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Plot spatial expression for multiple genes in a grid.
    
    Parameters
    ----------
    adata : AnnData
        AnnData with spatial coordinates
    genes : list
        List of gene names
    ncols : int
        Number of columns in grid
    spot_size : float
        Spot size
    figsize : tuple, optional
        Figure size (auto-calculated if None)
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    n_genes = len(genes)
    nrows = (n_genes + ncols - 1) // ncols
    
    if figsize is None:
        figsize = (ncols * 4, nrows * 3)
    
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    axes = axes.flatten() if n_genes > 1 else [axes]
    
    coords = adata.obsm['spatial']
    
    for i, gene in enumerate(genes):
        if gene not in adata.var_names:
            continue
        
        expr = adata[:, gene].X
        if hasattr(expr, 'toarray'):
            expr = expr.toarray().flatten()
        
        scatter = axes[i].scatter(
            coords[:, 0],
            coords[:, 1],
            c=expr,
            s=spot_size,
            cmap='viridis',
            alpha=0.8
        )
        plt.colorbar(scatter, ax=axes[i])
        axes[i].set_title(gene)
    
    # Hide unused subplots
    for i in range(n_genes, len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None


def plot_interactive_spatial(
    adata: ad.AnnData,
    gene: str,
    title: Optional[str] = None
) -> go.Figure:
    """
    Create interactive Plotly spatial plot.
    
    Parameters
    ----------
    adata : AnnData
        AnnData with spatial coordinates
    gene : str
        Gene name
    title : str, optional
        Plot title
        
    Returns
    -------
    fig : go.Figure
        Plotly figure object
    """
    if gene not in adata.var_names:
        raise ValueError(f"Gene {gene} not found in AnnData")
    
    coords = adata.obsm['spatial']
    expr = adata[:, gene].X
    
    if hasattr(expr, 'toarray'):
        expr = expr.toarray().flatten()
    
    fig = go.Figure(data=go.Scatter(
        x=coords[:, 0],
        y=coords[:, 1],
        mode='markers',
        marker=dict(
            size=10,
            color=expr,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title=f"{gene} expression")
        ),
        text=[f"Expr: {e:.2f}" for e in expr],
        hovertemplate='X: %{x}<br>Y: %{y}<br>%{text}<extra></extra>'
    ))
    
    if title is None:
        title = f"Spatial expression: {gene}"
    fig.update_layout(
        title=title,
        xaxis_title="X coordinate",
        yaxis_title="Y coordinate",
        hovermode='closest'
    )
    
    return fig


def plot_transport_plan(
    transport_plan: np.ndarray,
    spot_coords: np.ndarray,
    cell_coords: np.ndarray,
    threshold: float = 0.01,
    figsize: tuple = (10, 8),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Visualize transport plan as connections between spots and cells.
    
    Parameters
    ----------
    transport_plan : ndarray
        Transport plan matrix (n_spots x n_cells)
    spot_coords : ndarray
        Spot coordinates
    cell_coords : ndarray
        Cell coordinates
    threshold : float
        Minimum transport mass to draw edge
    figsize : tuple
        Figure size
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot spots
    ax.scatter(spot_coords[:, 0], spot_coords[:, 1], 
               c='red', s=100, label='Spots', alpha=0.7)
    
    # Plot cells
    ax.scatter(cell_coords[:, 0], cell_coords[:, 1],
               c='blue', s=30, label='Cells', alpha=0.7)
    
    # Plot transport edges
    for i in range(transport_plan.shape[0]):
        for j in range(transport_plan.shape[1]):
            if transport_plan[i, j] > threshold:
                alpha = min(transport_plan[i, j] * 10, 1.0)
                ax.plot(
                    [spot_coords[i, 0], cell_coords[j, 0]],
                    [spot_coords[i, 1], cell_coords[j, 1]],
                    'gray', alpha=alpha, linewidth=0.5
                )
    
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    ax.set_title("Transport Plan Visualization")
    ax.legend()
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None
