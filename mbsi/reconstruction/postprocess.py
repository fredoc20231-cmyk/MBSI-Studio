"""
Post-processing utilities for reconstructed expression.

Provides functions for quality control, normalization, and
analysis of reconstructed single-cell data.
"""

from typing import Optional, Dict, Any

import anndata as ad
import numpy as np
import scanpy as sc


def postprocess_reconstruction(
    reconstructed_adata: ad.AnnData,
    normalize: bool = True,
    log_transform: bool = True,
    filter_genes: bool = True,
    min_genes: int = 10,
    min_cells: int = 3
) -> ad.AnnData:
    """
    Post-process reconstructed expression data.
    
    Parameters
    ----------
    reconstructed_adata : AnnData
        Reconstructed cell-level AnnData
    normalize : bool
        If True, normalize expression (CPM or library size)
    log_transform : bool
        If True, apply log1p transformation
    filter_genes : bool
        If True, filter lowly expressed genes
    min_genes : int
        Minimum genes per cell for filtering
    min_cells : int
        Minimum cells per gene for filtering
        
    Returns
    -------
    processed_adata : AnnData
        Post-processed AnnData
    """
    processed = reconstructed_adata.copy()
    
    # Filter cells and genes
    if filter_genes:
        sc.pp.filter_cells(processed, min_genes=min_genes)
        sc.pp.filter_genes(processed, min_cells=min_cells)
    
    # Normalize
    if normalize:
        sc.pp.normalize_total(processed, target_sum=1e4)
    
    # Log transform
    if log_transform:
        sc.pp.log1p(processed)
    
    return processed


def compute_quality_metrics(
    reconstructed_adata: ad.AnnData,
    spot_adata: ad.AnnData
) -> Dict[str, Any]:
    """
    Compute quality metrics for reconstruction.
    
    Parameters
    ----------
    reconstructed_adata : AnnData
        Reconstructed cell-level data
    spot_adata : AnnData
        Original spot-level data
        
    Returns
    -------
    metrics : dict
        Quality metrics including:
        - n_cells: number of reconstructed cells
        - n_genes: number of genes
        - total_counts: total UMI counts
        - mean_counts_per_cell: average counts per cell
        - sparsity: fraction of zero entries
        - reconstruction_error: L2 error vs aggregated spots
    """
    metrics = {}
    
    # Basic stats
    metrics['n_cells'] = reconstructed_adata.n_obs
    metrics['n_genes'] = reconstructed_adata.n_vars
    
    # Count statistics
    X = reconstructed_adata.X
    if hasattr(X, 'toarray'):
        X = X.toarray()
    
    metrics['total_counts'] = float(X.sum())
    metrics['mean_counts_per_cell'] = float(X.mean(axis=1).mean())
    metrics['sparsity'] = float((X == 0).sum() / X.size)
    
    # Reconstruction error (aggregate cells back to spots)
    from mbsi.benchmarks.pseudo_visium import aggregate_cells_to_spots
    pseudo_spots = aggregate_cells_to_spots(
        reconstructed_adata,
        spot_adata.obsm['spatial']
    )
    
    # Align genes
    common_genes = [g for g in reconstructed_adata.var_names if g in spot_adata.var_names]
    if len(common_genes) > 0:
        error = np.linalg.norm(
            pseudo_spots[:, common_genes].X - 
            spot_adata[:, common_genes].X
        )
        metrics['reconstruction_error'] = float(error)
    else:
        metrics['reconstruction_error'] = None
    
    return metrics


def add_cell_type_annotations(
    reconstructed_adata: ad.AnnData,
    reference_adata: Optional[ad.AnnData] = None,
    method: str = "knn"
) -> ad.AnnData:
    """
    Add cell type annotations to reconstructed data.
    
    Parameters
    ----------
    reconstructed_adata : AnnData
        Reconstructed cell-level data
    reference_adata : AnnData, optional
        Reference single-cell data with cell types
    method : str
        Annotation method: 'knn' or 'marker'
        
    Returns
    -------
    annotated_adata : AnnData
        AnnData with cell type annotations in obs['cell_type']
    """
    annotated = reconstructed_adata.copy()
    
    if reference_adata is None:
        # Simple clustering-based annotation
        sc.pp.pca(annotated)
        sc.pp.neighbors(annotated)
        sc.tl.leiden(annotated, resolution=0.5)
        annotated.obs['cell_type'] = annotated.obs['leiden']
    else:
        # KNN-based annotation using reference
        if method == "knn":
            # Simple KNN matching
            from sklearn.neighbors import NearestNeighbors
            
            # Align genes
            common_genes = list(
                set(annotated.var_names) & set(reference_adata.var_names)
            )
            
            if len(common_genes) > 0:
                annotated = annotated[:, common_genes].copy()
                ref_subset = reference_adata[:, common_genes].copy()
                
                # Normalize
                sc.pp.normalize_total(annotated, target_sum=1e4)
                sc.pp.normalize_total(ref_subset, target_sum=1e4)
                sc.pp.log1p(annotated)
                sc.pp.log1p(ref_subset)
                
                # KNN
                nbrs = NearestNeighbors(n_neighbors=5)
                nbrs.fit(ref_subset.X)
                distances, indices = nbrs.kneighbors(annotated.X)
                
                # Majority vote
                if 'cell_type' in ref_subset.obs:
                    cell_types = []
                    for idx in indices:
                        types = ref_subset.obs['cell_type'].iloc[idx].values
                        most_common = np.bincount(types).argmax()
                        cell_types.append(most_common)
                    annotated.obs['cell_type'] = cell_types
                else:
                    annotated.obs['cell_type'] = 'unknown'
            else:
                annotated.obs['cell_type'] = 'unknown'
    
    return annotated


def compute_gene_statistics(
    reconstructed_adata: ad.AnnData
) -> ad.AnnData:
    """
    Compute gene-level statistics.
    
    Parameters
    ----------
    reconstructed_adata : AnnData
        Reconstructed cell-level data
        
    Returns
    -------
    adata : AnnData
        AnnData with gene statistics in var
    """
    adata = reconstructed_adata.copy()
    
    X = adata.X
    if hasattr(X, 'toarray'):
        X = X.toarray()
    
    # Compute statistics
    adata.var['mean_expression'] = X.mean(axis=0)
    adata.var['std_expression'] = X.std(axis=0)
    adata.var['n_cells_expressing'] = (X > 0).sum(axis=0)
    adata.var['fraction_expressing'] = (X > 0).sum(axis=0) / adata.n_obs
    
    return adata


def export_to_csv(
    reconstructed_adata: ad.AnnData,
    output_path: str
):
    """
    Export reconstructed data to CSV format.
    
    Parameters
    ----------
    reconstructed_adata : AnnData
        Reconstructed cell-level data
    output_path : str
        Path for output CSV (without extension)
    """
    import pandas as pd
    
    # Expression matrix
    X = reconstructed_adata.X
    if hasattr(X, 'toarray'):
        X = X.toarray()
    
    expr_df = pd.DataFrame(
        X,
        index=reconstructed_adata.obs_names,
        columns=reconstructed_adata.var_names
    )
    expr_df.to_csv(f"{output_path}_expression.csv")
    
    # Spatial coordinates
    coords_df = pd.DataFrame(
        reconstructed_adata.obsm['spatial'],
        index=reconstructed_adata.obs_names,
        columns=['x', 'y']
    )
    coords_df.to_csv(f"{output_path}_coordinates.csv")
    
    # Metadata
    if 'cell_type' in reconstructed_adata.obs:
        metadata_df = reconstructed_adata.obs[['cell_type']]
        metadata_df.to_csv(f"{output_path}_metadata.csv")
