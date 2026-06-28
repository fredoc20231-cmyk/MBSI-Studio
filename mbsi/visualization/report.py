"""
Report generation for MBSI results.

Generates HTML reports and publication-ready figures.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import json

import anndata as ad
import pandas as pd
from jinja2 import Template

from mbsi.utils import to_dense_array
from mbsi.visualization.spatial_plots import (
    plot_spatial_gene,
    plot_reconstruction_scatter,
    plot_spatial_comparison
)
from mbsi.visualization.benchmark_plots import (
    plot_benchmark_summary,
    plot_ablation_results,
    plot_radar_chart
)


def generate_html_report(
    reconstructed_adata: ad.AnnData,
    spot_adata: ad.AnnData,
    metrics: Dict[str, Any],
    output_path: str,
    title: str = "MBSI Reconstruction Report"
):
    """
    Generate comprehensive HTML report.
    
    Parameters
    ----------
    reconstructed_adata : AnnData
        Reconstructed cell-level data
    spot_adata : AnnData
        Original spot-level data
    metrics : dict
        Benchmark metrics
    output_path : str
        Path for HTML output
    title : str
        Report title
    """
    # Create figures directory
    output_dir = Path(output_path).parent
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    
    # Generate figures
    figures = {}
    
    # Top genes
    from scanpy.pp import high_variable_genes
    temp_adata = reconstructed_adata.copy()
    high_variable_genes(temp_adata, n_top_genes=5)
    top_genes = temp_adata.var['highly_variable'].index.tolist()[:5]
    
    for i, gene in enumerate(top_genes):
        if gene in reconstructed_adata.var_names:
            fig = plot_spatial_gene(reconstructed_adata, gene, return_fig=True)
            fig_path = figures_dir / f"gene_{i}.png"
            fig.savefig(fig_path, dpi=150, bbox_inches='tight')
            figures[gene] = f"figures/gene_{i}.png"
    
    # HTML template
    template_str = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; }
        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: #ecf0f1; border-radius: 5px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #3498db; }
        .metric-label { font-size: 14px; color: #7f8c8d; }
        .figure { margin: 20px 0; text-align: center; }
        .figure img { max-width: 100%; border: 1px solid #bdc3c7; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    
    <h2>Summary</h2>
    <p>Reconstruction completed with {{ n_cells }} cells and {{ n_genes }} genes.</p>
    
    <h2>Performance Metrics</h2>
    <div>
        {% for key, value in metrics.items() %}
        {% if value is not none and value is not mapping %}
        <div class="metric">
            <div class="metric-value">{{ value | round(3) }}</div>
            <div class="metric-label">{{ key }}</div>
        </div>
        {% endif %}
        {% endfor %}
    </div>
    
    <h2>Parameters</h2>
    <table>
        {% for key, value in parameters.items() %}
        <tr>
            <td>{{ key }}</td>
            <td>{{ value }}</td>
        </tr>
        {% endfor %}
    </table>
    
    <h2>Spatial Expression</h2>
    {% for gene, path in figures.items() %}
    <div class="figure">
        <h3>{{ gene }}</h3>
        <img src="{{ path }}" alt="{{ gene }}">
    </div>
    {% endfor %}
    
    <h2>Convergence</h2>
    <p>Iterations: {{ convergence.iterations }}</p>
    <p>Converged: {{ convergence.converged }}</p>
    <p>Final Objective: {{ convergence.objective | round(4) }}</p>
    
</body>
</html>
    """
    
    template = Template(template_str)
    
    # Render template
    html = template.render(
        title=title,
        n_cells=reconstructed_adata.n_obs,
        n_genes=reconstructed_adata.n_vars,
        metrics=metrics,
        parameters=reconstructed_adata.uns.get('parameters', {}),
        figures=figures,
        convergence=reconstructed_adata.uns.get('convergence', {})
    )
    
    # Save HTML
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"Report saved to {output_path}")


def export_nature_figures(
    reconstructed_adata: ad.AnnData,
    spot_adata: ad.AnnData,
    output_dir: str,
    dpi: int = 300
):
    """
    Export publication-ready figures in Nature style.
    
    Parameters
    ----------
    reconstructed_adata : AnnData
        Reconstructed data
    spot_adata : AnnData
        Original spot data
    output_dir : str
        Output directory for figures
    dpi : int
        DPI for figures
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Set publication style
    import matplotlib.pyplot as plt
    plt.style.use('seaborn-v0_8-paper')
    
    # Figure 1: Spatial comparison
    # Use variance-based gene selection instead of deprecated scanpy function
    import numpy as np
    X = to_dense_array(reconstructed_adata.X)
    gene_vars = np.var(X, axis=0)
    top_gene_idx = np.argmax(gene_vars)
    top_gene = reconstructed_adata.var_names[top_gene_idx]
    
    if top_gene in reconstructed_adata.var_names:
        fig = plot_spatial_comparison(
            spot_adata, reconstructed_adata, top_gene,
            figsize=(12, 5), return_fig=True
        )
        fig.savefig(output_path / "fig1_spatial_comparison.png",
                   dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    
    # Figure 2: Reconstruction scatter (skip if sizes don't match)
    if spot_adata.n_obs == reconstructed_adata.n_obs:
        fig = plot_reconstruction_scatter(
            spot_adata, reconstructed_adata, top_gene,
            figsize=(5, 5), return_fig=True
        )
        fig.savefig(output_path / "fig2_reconstruction_scatter.png",
                   dpi=dpi, bbox_inches='tight')
        plt.close(fig)
    
    print(f"Figures exported to {output_dir}")


def save_metrics_json(
    metrics: Dict[str, Any],
    output_path: str
):
    """
    Save metrics to JSON file.
    
    Parameters
    ----------
    metrics : dict
        Metrics dictionary
    output_path : str
        Output JSON path
    """
    # Convert numpy types to Python types
    def convert(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        else:
            return obj
    
    metrics_converted = convert(metrics)
    
    with open(output_path, 'w') as f:
        json.dump(metrics_converted, f, indent=2)
    
    print(f"Metrics saved to {output_path}")


def create_summary_table(
    results: List[Dict[str, Any]],
    output_path: str
):
    """
    Create summary table from multiple results.
    
    Parameters
    ----------
    results : list
        List of result dictionaries
    output_path : str
        Output CSV path
    """
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    print(f"Summary table saved to {output_path}")
