"""
Benchmark visualization plots.

Creates plots for benchmarking results, ablation studies,
and performance comparisons.
"""

from typing import Optional, Dict, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

DARK = {
    "paper_bgcolor": "#0d1828",
    "plot_bgcolor": "#07111f",
    "font": {"color": "#f4f7fb", "size": 10},
}


def plot_leaderboard_bars(leaderboard_df: pd.DataFrame, metric: str = "gene_pearson"):
    """Plotly bar chart for benchmark leaderboard (MBSI dark theme)."""
    if leaderboard_df.empty or metric not in leaderboard_df.columns:
        return None
    fig = go.Figure(data=go.Bar(
        x=leaderboard_df["method"],
        y=leaderboard_df[metric],
        marker_color=["#4f7cff" if m == "mbsi" else "#9aa7b8" for m in leaderboard_df["method"]],
    ))
    fig.update_layout(
        title=f"Leaderboard — {metric}",
        **DARK,
        height=360,
        margin=dict(l=40, r=20, t=40, b=80),
    )
    return fig


def plot_ground_truth_spatial(adata, color_col: str = "cell_type") -> go.Figure:
    coords = adata.obsm["spatial"]
    c = adata.obs[color_col].astype(str) if color_col in adata.obs.columns else None
    fig = px.scatter(x=coords[:, 0], y=coords[:, 1], color=c, title="Ground Truth Spatial")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(**DARK, height=380, margin=dict(l=40, r=20, t=40, b=40))
    return fig


def plot_pseudo_visium_spatial(pseudo_adata) -> go.Figure:
    coords = pseudo_adata.obsm["spatial"]
    totals = pseudo_adata.X.sum(axis=1)
    if hasattr(totals, "A1"):
        totals = totals.A1
    fig = px.scatter(x=coords[:, 0], y=coords[:, 1], color=totals, color_continuous_scale="Viridis", title="Pseudo-Visium")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(**DARK, height=380, margin=dict(l=40, r=20, t=40, b=40))
    return fig


def plot_readiness_gauge(score: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        title={"text": "Ground Truth Readiness"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#4f7cff"}},
    ))
    fig.update_layout(**DARK, height=280, margin=dict(l=30, r=30, t=50, b=20))
    return fig


def plot_spatial_error_map(coords, error_values, title: str = "Spatial Error") -> go.Figure:
    fig = px.scatter(x=coords[:, 0], y=coords[:, 1], color=error_values, color_continuous_scale="Reds", title=title)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(**DARK, height=380, margin=dict(l=40, r=20, t=40, b=40))
    return fig


def plot_boundary_preservation(leaderboard_df: pd.DataFrame) -> go.Figure:
    if leaderboard_df.empty or "boundary_preservation" not in leaderboard_df.columns:
        return plot_leaderboard_bars(leaderboard_df, "gene_pearson")
    fig = go.Figure(data=go.Bar(x=leaderboard_df["method"], y=leaderboard_df["boundary_preservation"], marker_color="#39d98a"))
    fig.update_layout(title="Boundary Preservation", **DARK, height=360, margin=dict(l=40, r=20, t=40, b=80))
    return fig


def plot_method_comparison_radar(leaderboard_df: pd.DataFrame) -> go.Figure:
    metrics = [m for m in ("gene_pearson", "cell_type_accuracy", "niche_preservation") if m in leaderboard_df.columns]
    if not metrics or leaderboard_df.empty:
        return plot_leaderboard_bars(leaderboard_df)
    fig = go.Figure()
    for _, row in leaderboard_df.head(4).iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[float(row.get(m, 0) or 0) for m in metrics],
            theta=metrics, fill="toself", name=str(row["method"]),
        ))
    fig.update_layout(title="Method Comparison", **DARK, height=400, margin=dict(l=40, r=40, t=40, b=40))
    return fig


def plot_benchmark_summary(
    metrics_df: pd.DataFrame,
    figsize: tuple = (12, 8),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Plot summary of benchmark metrics.
    
    Parameters
    ----------
    metrics_df : DataFrame
        DataFrame with metrics (one row per configuration)
    figsize : tuple
        Figure size
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    # Extract numeric metrics
    metric_cols = [col for col in metrics_df.columns 
                   if col not in ['configuration', 'use_sheaf', 'use_anisotropic', 'balanced']]
    
    if len(metric_cols) == 0:
        print("No numeric metrics found")
        return None
    
    n_metrics = len(metric_cols)
    nrows = (n_metrics + 1) // 2
    
    fig, axes = plt.subplots(nrows, 2, figsize=figsize)
    axes = axes.flatten() if n_metrics > 1 else [axes]
    
    for i, metric in enumerate(metric_cols):
        if i >= len(axes):
            break
        
        # Plot bar chart
        ax = axes[i]
        
        # Handle nested metrics (e.g., from compute_all_metrics)
        values = []
        for _, row in metrics_df.iterrows():
            val = row.get(metric)
            if isinstance(val, dict):
                # Take first value if dict
                val = list(val.values())[0] if val else 0
            values.append(float(val) if val is not None else 0)
        
        configs = metrics_df['configuration'].values
        
        bars = ax.bar(range(len(configs)), values)
        ax.set_xticks(range(len(configs)))
        ax.set_xticklabels(configs, rotation=45, ha='right')
        ax.set_ylabel(metric)
        ax.set_title(f"{metric} by Configuration")
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.3f}', ha='center', va='bottom', fontsize=8)
    
    # Hide unused subplots
    for i in range(n_metrics, len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None


def plot_ablation_results(
    ablation_df: pd.DataFrame,
    figsize: tuple = (14, 10),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Plot ablation study results.
    
    Parameters
    ----------
    ablation_df : DataFrame
        DataFrame with ablation results
    figsize : tuple
        Figure size
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    # Extract key metrics
    key_metrics = ['pearson_correlation', 'rmse', 'r2_score']
    available_metrics = [m for m in key_metrics if m in ablation_df.columns]
    
    if len(available_metrics) == 0:
        print("No key metrics found for ablation plot")
        return None
    
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    
    # Plot 1: Bar chart of correlations
    ax = axes[0, 0]
    if 'pearson_correlation' in ablation_df.columns:
        configs = ablation_df['configuration'].values
        corrs = ablation_df['pearson_correlation'].values
        
        bars = ax.bar(range(len(configs)), corrs)
        ax.set_xticks(range(len(configs)))
        ax.set_xticklabels(configs, rotation=45, ha='right')
        ax.set_ylabel('Pearson Correlation')
        ax.set_title('Reconstruction Correlation')
        ax.set_ylim([0, 1])
        
        for bar, corr in zip(bars, corrs):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{corr:.3f}', ha='center', va='bottom')
    
    # Plot 2: RMSE
    ax = axes[0, 1]
    if 'rmse' in ablation_df.columns:
        configs = ablation_df['configuration'].values
        rmses = ablation_df['rmse'].values
        
        bars = ax.bar(range(len(configs)), rmses, color='orange')
        ax.set_xticks(range(len(configs)))
        ax.set_xticklabels(configs, rotation=45, ha='right')
        ax.set_ylabel('RMSE')
        ax.set_title('Reconstruction Error')
        
        for bar, rmse in zip(bars, rmses):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{rmse:.3f}', ha='center', va='bottom')
    
    # Plot 3: R² score
    ax = axes[1, 0]
    if 'r2_score' in ablation_df.columns:
        configs = ablation_df['configuration'].values
        r2s = ablation_df['r2_score'].values
        
        bars = ax.bar(range(len(configs)), r2s, color='green')
        ax.set_xticks(range(len(configs)))
        ax.set_xticklabels(configs, rotation=45, ha='right')
        ax.set_ylabel('R² Score')
        ax.set_title('R² Score')
        
        for bar, r2 in zip(bars, r2s):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{r2:.3f}', ha='center', va='bottom')
    
    # Plot 4: Component contribution
    ax = axes[1, 1]
    if all(col in ablation_df.columns for col in ['use_sheaf', 'use_anisotropic']):
        # Group by configuration type
        full_mbsi = ablation_df[ablation_df['configuration'] == 'Full MBSI']
        if len(full_mbsi) > 0:
            baseline = full_mbsi['pearson_correlation'].values[0]
            
            contributions = {}
            for _, row in ablation_df.iterrows():
                config = row['configuration']
                if config != 'Full MBSI':
                    contributions[config] = row['pearson_correlation'] - baseline
            
            if contributions:
                ax.barh(list(contributions.keys()), list(contributions.values()))
                ax.axvline(x=0, color='red', linestyle='--')
                ax.set_xlabel('Change in Correlation')
                ax.set_title('Component Contribution')
    
    plt.tight_layout()
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None


def plot_radar_chart(
    metrics_df: pd.DataFrame,
    metrics: Optional[list] = None,
    figsize: tuple = (8, 8),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Create radar chart for comparing configurations.
    
    Parameters
    ----------
    metrics_df : DataFrame
        DataFrame with metrics
    metrics : list, optional
        List of metrics to include
    figsize : tuple
        Figure size
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    if metrics is None:
        metrics = ['pearson_correlation', 'spearman_correlation', 'r2_score']
        metrics = [m for m in metrics if m in metrics_df.columns]
    
    if len(metrics) < 3:
        print("Need at least 3 metrics for radar chart")
        return None
    
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))
    
    # Number of variables
    n_vars = len(metrics)
    
    # Compute angle for each axis
    angles = np.linspace(0, 2 * np.pi, n_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete the circle
    
    # Plot each configuration
    for _, row in metrics_df.iterrows():
        values = []
        for metric in metrics:
            val = row.get(metric)
            if isinstance(val, dict):
                val = list(val.values())[0] if val else 0
            values.append(float(val) if val is not None else 0)
        
        values += values[:1]
        
        ax.plot(angles, values, 'o-', linewidth=2, label=row['configuration'])
        ax.fill(angles, values, alpha=0.25)
    
    # Set labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1)
    ax.set_title('Configuration Comparison')
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None


def plot_parameter_sweep(
    sweep_df: pd.DataFrame,
    parameter: str,
    metric: str = 'pearson_correlation',
    figsize: tuple = (10, 6),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Plot parameter sweep results.
    
    Parameters
    ----------
    sweep_df : DataFrame
        DataFrame with sweep results
    parameter : str
        Parameter that was swept
    metric : str
        Metric to plot
    figsize : tuple
        Figure size
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    if parameter not in sweep_df.columns or metric not in sweep_df.columns:
        print(f"Parameter {parameter} or metric {metric} not found")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    param_values = sweep_df[parameter].values
    metric_values = sweep_df[metric].values
    
    ax.plot(param_values, metric_values, 'o-', linewidth=2, markersize=8)
    ax.set_xlabel(parameter)
    ax.set_ylabel(metric)
    ax.set_title(f'{metric} vs {parameter}')
    ax.grid(True, alpha=0.3)
    
    # Mark best value
    best_idx = np.argmax(metric_values) if 'correlation' in metric or 'r2' in metric else np.argmin(metric_values)
    ax.scatter(param_values[best_idx], metric_values[best_idx], 
              color='red', s=100, zorder=5, label='Best')
    ax.legend()
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None


def plot_boundary_leakage(
    metrics_df: pd.DataFrame,
    figsize: tuple = (8, 6),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Plot boundary leakage scores for different configurations.
    
    Parameters
    ----------
    metrics_df : DataFrame
        DataFrame with boundary leakage metric
    figsize : tuple
        Figure size
    return_fig : bool
        If True, return figure object
        
    Returns
    -------
    fig : plt.Figure, optional
        Figure object if return_fig=True
    """
    if 'boundary_leakage' not in metrics_df.columns:
        print("boundary_leakage metric not found")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    configs = metrics_df['configuration'].values
    leakages = metrics_df['boundary_leakage'].values
    
    bars = ax.bar(range(len(configs)), leakages, color='coral')
    ax.set_xticks(range(len(configs)))
    ax.set_xticklabels(configs, rotation=45, ha='right')
    ax.set_ylabel('Boundary Leakage Score')
    ax.set_title('Boundary Leakage by Configuration')
    ax.set_ylim([0, 1])
    
    for bar, leakage in zip(bars, leakages):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{leakage:.3f}', ha='center', va='bottom')
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None


def plot_convergence(
    convergence_log: Dict[str, Any],
    figsize: tuple = (10, 6),
    return_fig: bool = False
) -> Optional[plt.Figure]:
    """
    Plot convergence of optimization.
    
    Parameters
    ----------
    convergence_log : dict
        Convergence log from reconstruction
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
    
    # For MVP, just show final objective
    # Full implementation would track objective over iterations
    objective = convergence_log.get('objective', 0)
    iterations = convergence_log.get('iterations', 0)
    converged = convergence_log.get('converged', False)
    
    ax.bar(['Objective'], [objective])
    ax.set_ylabel('Objective Value')
    ax.set_title(f'Optimization Convergence ({"Converged" if converged else "Not Converged"})')
    
    # Add iteration info
    ax.text(0, objective, f'n={iterations}', ha='center', va='bottom')
    
    if return_fig:
        return fig
    else:
        plt.show()
        return None
