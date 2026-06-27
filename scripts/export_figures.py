"""
Export figures script for generating publication-ready visualizations.
"""

import sys
from pathlib import Path
import argparse

import anndata as ad

sys.path.insert(0, str(Path(__file__).parent.parent))

from mbsi.visualization.spatial_plots import (
    plot_spatial_gene,
    plot_reconstruction_scatter,
    plot_spatial_comparison,
    plot_multiple_genes
)
from mbsi.visualization.benchmark_plots import (
    plot_benchmark_summary,
    plot_ablation_results
)
from mbsi.visualization.report import export_nature_figures


def export_all_figures(
    reconstructed_path: str,
    spot_path: str,
    output_dir: str = "data/figures",
    dpi: int = 300
):
    """
    Export all figures for publication.
    
    Parameters
    ----------
    reconstructed_path : str
        Path to reconstructed AnnData
    spot_path : str
        Path to original spot AnnData
    output_dir : str
        Output directory for figures
    dpi : int
        DPI for figures
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    reconstructed = ad.read_h5ad(reconstructed_path)
    spot_adata = ad.read_h5ad(spot_path)
    
    print("Exporting publication-ready figures...")
    
    export_nature_figures(reconstructed, spot_adata, output_path, dpi=dpi)
    
    print(f"Figures exported to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export publication figures")
    parser.add_argument("--reconstructed", required=True, help="Path to reconstructed h5ad")
    parser.add_argument("--spots", required=True, help="Path to spot h5ad")
    parser.add_argument("--output", default="data/figures", help="Output directory")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for figures")
    
    args = parser.parse_args()
    
    export_all_figures(args.reconstructed, args.spots, args.output, args.dpi)
