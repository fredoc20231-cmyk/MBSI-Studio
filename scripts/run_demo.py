"""
Demo dataset generation and pipeline test.

Generates a synthetic spatial transcriptomics dataset and runs
the complete MBSI pipeline to demonstrate functionality.
"""

import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mbsi.reconstruction.solver import run_mbsi
from mbsi.benchmarks.pseudo_visium import make_pseudo_visium
from mbsi.benchmarks.metrics import compute_all_metrics
from mbsi.visualization.spatial_plots import plot_spatial_gene, plot_reconstruction_scatter
from mbsi.visualization.report import export_nature_figures


def generate_demo_dataset(
    n_cells: int = 200,
    n_spots: int = 40,
    n_genes: int = 100,
    n_compartments: int = 2,
    n_marker_genes: int = 5,
    ambient_rna_level: float = 0.1,
    random_state: int = 42
) -> tuple:
    """
    Generate synthetic demo dataset with known ground truth.
    
    Parameters
    ----------
    n_cells : int
        Number of cells
    n_spots : int
        Number of spots
    n_genes : int
        Number of genes
    n_compartments : int
        Number of tissue compartments
    n_marker_genes : int
        Number of marker genes per compartment
    ambient_rna_level : float
        Level of ambient RNA contamination
    random_state : int
        Random seed
        
    Returns
    -------
    true_adata : AnnData
        Ground truth single-cell data
    spot_adata : AnnData
        Pseudo-Visium spot data
    """
    np.random.seed(random_state)
    
    print(f"Generating demo dataset: {n_cells} cells, {n_spots} spots, {n_genes} genes")
    
    # Generate spatial coordinates for cells
    # Create two compartments
    cell_coords = np.zeros((n_cells, 2))
    cell_labels = np.zeros(n_cells, dtype=int)
    
    cells_per_compartment = n_cells // n_compartments
    
    for comp in range(n_compartments):
        start_idx = comp * cells_per_compartment
        end_idx = (comp + 1) * cells_per_compartment if comp < n_compartments - 1 else n_cells
        
        # Compartment centers
        center_x = comp * 100 + 50
        center_y = 50
        
        # Generate cells around compartment center
        for i in range(start_idx, end_idx):
            cell_coords[i, 0] = center_x + np.random.normal(0, 20)
            cell_coords[i, 1] = center_y + np.random.normal(0, 20)
            cell_labels[i] = comp
    
    # Generate gene expression
    # Base expression for all genes
    base_expression = np.random.exponential(1.0, size=(n_cells, n_genes))
    
    # Add compartment-specific marker genes
    marker_genes_per_comp = n_marker_genes // n_compartments
    
    for comp in range(n_compartments):
        start_gene = comp * marker_genes_per_comp
        end_gene = (comp + 1) * marker_genes_per_comp if comp < n_compartments - 1 else n_marker_genes
        
        # High expression in this compartment
        comp_cells = (cell_labels == comp)
        base_expression[comp_cells, start_gene:end_gene] *= 10
        
        # Low expression in other compartments
        base_expression[~comp_cells, start_gene:end_gene] *= 0.1
    
    # Add ambient RNA
    ambient = np.random.exponential(ambient_rna_level, size=(n_cells, n_genes))
    expression = base_expression + ambient
    
    # Create single-cell AnnData
    true_adata = ad.AnnData(X=expression, dtype=np.float32)
    true_adata.var_names = [f"gene_{i}" for i in range(n_genes)]
    true_adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
    true_adata.obsm['spatial'] = cell_coords
    true_adata.obs['label'] = pd.Categorical(cell_labels)
    true_adata.obs['compartment'] = [f"compartment_{cell_labels[i]}" for i in range(n_cells)]
    
    # Generate pseudo-Visium spots
    print("Generating pseudo-Visium spots...")
    spot_adata = make_pseudo_visium(
        true_adata,
        spot_diameter=55.0,
        aggregation="hex",
        n_spots=n_spots,
        random_state=random_state
    )
    
    print(f"Generated {spot_adata.n_obs} spots from {n_cells} cells")
    
    return true_adata, spot_adata


def run_demo_pipeline(
    output_dir: str = "data/demo",
    random_state: int = 42
):
    """
    Run complete demo pipeline.
    
    Parameters
    ----------
    output_dir : str
        Output directory for results
    random_state : int
        Random seed
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("MBSI Studio Demo Pipeline")
    print("=" * 60)
    
    # Step 1: Generate demo dataset
    print("\n[Step 1] Generating demo dataset...")
    true_adata, spot_adata = generate_demo_dataset(random_state=random_state)
    
    # Save ground truth
    true_adata.write_h5ad(output_path / "true_single_cell.h5ad")
    spot_adata.write_h5ad(output_path / "pseudo_visium_spots.h5ad")
    
    print(f"Saved ground truth to {output_path}")
    print(f"  - True single-cell: {true_adata.n_obs} cells, {true_adata.n_vars} genes")
    print(f"  - Pseudo-Visium: {spot_adata.n_obs} spots, {spot_adata.n_vars} genes")
    
    # Step 2: Run MBSI reconstruction
    print("\n[Step 2] Running MBSI reconstruction...")
    reconstructed = run_mbsi(
        spot_adata,
        n_cells_per_spot=5,
        gamma=1.0,
        epsilon=0.05,
        lambda_sheaf=0.1,
        use_sheaf=True,
        use_anisotropic=False,  # No image for demo
        random_state=random_state
    )
    
    # Save reconstruction
    reconstructed.write_h5ad(output_path / "reconstructed.h5ad")
    print(f"Saved reconstruction: {reconstructed.n_obs} cells, {reconstructed.n_vars} genes")
    
    # Step 3: Compute validation metrics
    print("\n[Step 3] Computing validation metrics...")
    metrics = compute_all_metrics(true_adata, reconstructed)
    
    print("Validation Metrics:")
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:.4f}")
    
    # Save metrics
    import json
    with open(output_path / "metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    # Step 4: Generate figures
    print("\n[Step 4] Generating figures...")
    figures_dir = output_path / "figures"
    figures_dir.mkdir(exist_ok=True)
    
    # Get top marker genes (use variance-based selection)
    gene_vars = np.var(true_adata.X.toarray() if hasattr(true_adata.X, 'toarray') else true_adata.X, axis=0)
    top_gene_indices = np.argsort(gene_vars)[-3:][::-1]
    top_genes = [true_adata.var_names[i] for i in top_gene_indices]
    
    import matplotlib.pyplot as plt
    
    for i, gene in enumerate(top_genes):
        if gene in reconstructed.var_names:
            # Spatial plot
            fig = plot_spatial_gene(reconstructed, gene, return_fig=True)
            fig.savefig(figures_dir / f"recon_{gene}.png", dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            # Scatter plot (skip if sizes don't match)
            if gene in true_adata.var_names and true_adata.n_obs == reconstructed.n_obs:
                fig = plot_reconstruction_scatter(true_adata, reconstructed, gene, return_fig=True)
                fig.savefig(figures_dir / f"scatter_{gene}.png", dpi=150, bbox_inches='tight')
                plt.close(fig)
    
    print(f"Saved figures to {figures_dir}")
    
    # Step 5: Export publication figures
    print("\n[Step 5] Exporting publication-ready figures...")
    export_nature_figures(reconstructed, spot_adata, figures_dir, dpi=300)
    
    print("\n" + "=" * 60)
    print("Demo pipeline completed successfully!")
    print("=" * 60)
    print(f"\nResults saved to: {output_path}")
    print("  - true_single_cell.h5ad (ground truth)")
    print("  - pseudo_visium_spots.h5ad (input spots)")
    print("  - reconstructed.h5ad (MBSI output)")
    print("  - metrics.json (validation metrics)")
    print("  - figures/ (visualization figures)")
    
    return true_adata, spot_adata, reconstructed, metrics


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run MBSI Studio demo")
    parser.add_argument("--output-dir", default="data/demo", help="Output directory")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    run_demo_pipeline(output_dir=args.output_dir, random_state=args.random_state)
