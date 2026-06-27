"""Visualization module for spatial plots and benchmark figures."""

from mbsi.visualization.spatial_plots import plot_spatial_gene, plot_reconstruction_scatter
from mbsi.visualization.benchmark_plots import plot_benchmark_summary, plot_ablation_results
from mbsi.visualization.report import generate_html_report, export_nature_figures

__all__ = [
    "plot_spatial_gene",
    "plot_reconstruction_scatter",
    "plot_benchmark_summary",
    "plot_ablation_results",
    "generate_html_report",
    "export_nature_figures"
]
