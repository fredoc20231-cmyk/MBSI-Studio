"""
Benchmark script for running comprehensive validation and ablation studies.
"""

import sys
from pathlib import Path
import argparse

import anndata as ad
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from mbsi.benchmarks.ablation import run_ablation_suite
from mbsi.benchmarks.metrics import compute_all_metrics
from mbsi.visualization.benchmark_plots import (
    plot_benchmark_summary,
    plot_ablation_results,
    plot_radar_chart
)


def run_full_benchmark(
    spot_adata_path: str,
    true_adata_path: str,
    output_dir: str = "data/benchmarks"
):
    """
    Run full benchmark suite including ablation study.
    
    Parameters
    ----------
    spot_adata_path : str
        Path to spot-level AnnData
    true_adata_path : str
        Path to ground truth single-cell AnnData
    output_dir : str
        Output directory for results
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("MBSI Studio Benchmark Suite")
    print("=" * 60)
    
    # Load data
    print("\nLoading data...")
    spot_adata = ad.read_h5ad(spot_adata_path)
    true_adata = ad.read_h5ad(true_adata_path)
    
    print(f"Spot data: {spot_adata.n_obs} spots, {spot_adata.n_vars} genes")
    print(f"True data: {true_adata.n_obs} cells, {true_adata.n_vars} genes")
    
    # Run ablation study
    print("\nRunning ablation study...")
    ablation_results = run_ablation_suite(
        spot_adata,
        true_adata,
        output_path / "ablation_results.csv"
    )
    
    print("Ablation Results:")
    print(ablation_results[['configuration', 'pearson_correlation', 'rmse', 'r2_score']])
    
    # Generate benchmark plots
    print("\nGenerating benchmark plots...")
    figures_dir = output_path / "figures"
    figures_dir.mkdir(exist_ok=True)
    
    import matplotlib.pyplot as plt
    
    # Summary plot
    fig = plot_benchmark_summary(ablation_results, return_fig=True)
    fig.savefig(figures_dir / "benchmark_summary.png", dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Ablation plot
    fig = plot_ablation_results(ablation_results, return_fig=True)
    fig.savefig(figures_dir / "ablation_results.png", dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Radar chart
    fig = plot_radar_chart(ablation_results, return_fig=True)
    fig.savefig(figures_dir / "radar_chart.png", dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"\nBenchmark completed. Results saved to {output_path}")
    print(f"  - ablation_results.csv")
    print(f"  - figures/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MBSI benchmark suite")
    parser.add_argument("--spots", required=True, help="Path to spot-level h5ad file")
    parser.add_argument("--true", required=True, help="Path to ground truth h5ad file")
    parser.add_argument("--output", default="data/benchmarks", help="Output directory")
    
    args = parser.parse_args()
    
    run_full_benchmark(args.spots, args.true, args.output)
