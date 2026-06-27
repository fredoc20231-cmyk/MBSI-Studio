"""
Ablation study for MBSI components.

Runs different configurations to understand the contribution
of each component to overall performance.
"""

from typing import Dict, Any, List
import pandas as pd

import anndata as ad
import numpy as np

from mbsi.reconstruction.solver import run_mbsi
from mbsi.benchmarks.metrics import compute_all_metrics


def run_ablation_suite(
    spot_adata: ad.AnnData,
    true_adata: ad.AnnData,
    cell_coords: np.ndarray = None,
    image: np.ndarray = None,
    output_path: str = None
) -> pd.DataFrame:
    """
    Run complete ablation study comparing different MBSI configurations.
    
    Parameters
    ----------
    spot_adata : AnnData
        Spot-level data
    true_adata : AnnData
        Ground truth single-cell data
    cell_coords : ndarray, optional
        True cell coordinates
    image : ndarray, optional
        Tissue image
    output_path : str, optional
        Path to save results CSV
        
    Returns
    -------
    results : DataFrame
        Comparison table of all ablation configurations
    """
    configurations = [
        {
            'name': 'Full MBSI',
            'use_sheaf': True,
            'use_anisotropic': True,
            'balanced': False
        },
        {
            'name': 'Isotropic Diffusion',
            'use_sheaf': True,
            'use_anisotropic': False,
            'balanced': False
        },
        {
            'name': 'No Sheaf Regularization',
            'use_sheaf': False,
            'use_anisotropic': True,
            'balanced': False
        },
        {
            'name': 'Balanced OT',
            'use_sheaf': True,
            'use_anisotropic': True,
            'balanced': True
        },
        {
            'name': 'Euclidean Kernel Baseline',
            'use_sheaf': False,
            'use_anisotropic': False,
            'balanced': False
        }
    ]
    
    results = []
    
    for config in configurations:
        print(f"Running: {config['name']}")
        
        # Run reconstruction with this configuration
        if config['balanced']:
            # Use balanced OT (strong marginal constraints)
            reconstructed = run_mbsi(
                spot_adata,
                cell_coords=cell_coords,
                image=image,
                use_sheaf=config['use_sheaf'],
                use_anisotropic=config['use_anisotropic'],
                rho1=1000,
                rho2=1000
            )
        else:
            reconstructed = run_mbsi(
                spot_adata,
                cell_coords=cell_coords,
                image=image,
                use_sheaf=config['use_sheaf'],
                use_anisotropic=config['use_anisotropic']
            )
        
        # Compute metrics
        metrics = compute_all_metrics(true_adata, reconstructed)
        
        # Add configuration info
        metrics['configuration'] = config['name']
        metrics['use_sheaf'] = config['use_sheaf']
        metrics['use_anisotropic'] = config['use_anisotropic']
        metrics['balanced'] = config['balanced']
        
        results.append(metrics)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    # Save if path provided
    if output_path:
        results_df.to_csv(output_path, index=False)
    
    return results_df


def run_parameter_sweep(
    spot_adata: ad.AnnData,
    true_adata: ad.AnnData,
    parameter: str,
    values: List[float],
    cell_coords: np.ndarray = None,
    image: np.ndarray = None
) -> pd.DataFrame:
    """
    Sweep over a single parameter to find optimal value.
    
    Parameters
    ----------
    spot_adata : AnnData
        Spot-level data
    true_adata : AnnData
        Ground truth single-cell data
    parameter : str
        Parameter to sweep ('gamma', 'epsilon', 'lambda_sheaf', etc.)
    values : list
        List of parameter values to test
    cell_coords : ndarray, optional
        Cell coordinates
    image : ndarray, optional
        Tissue image
        
    Returns
    -------
    results : DataFrame
        Results for each parameter value
    """
    results = []
    
    for value in values:
        print(f"Testing {parameter} = {value}")
        
        # Build kwargs
        kwargs = {
            'cell_coords': cell_coords,
            'image': image,
            parameter: value
        }
        
        # Run reconstruction
        reconstructed = run_mbsi(spot_adata, **kwargs)
        
        # Compute metrics
        metrics = compute_all_metrics(true_adata, reconstructed)
        metrics[parameter] = value
        
        results.append(metrics)
    
    results_df = pd.DataFrame(results)
    
    return results_df


def compare_kernel_types(
    spot_adata: ad.AnnData,
    true_adata: ad.AnnData,
    cell_coords: np.ndarray = None,
    image: np.ndarray = None
) -> pd.DataFrame:
    """
    Compare different kernel types.
    
    Parameters
    ----------
    spot_adata : AnnData
        Spot-level data
    true_adata : AnnData
        Ground truth
    cell_coords : ndarray, optional
        Cell coordinates
    image : ndarray, optional
        Tissue image
        
    Returns
    -------
    results : DataFrame
        Comparison of kernel types
    """
    kernel_types = [
        {'name': 'Anisotropic (MBSI)', 'use_anisotropic': True, 'image': image},
        {'name': 'Isotropic', 'use_anisotropic': False, 'image': None},
        {'name': 'Anisotropic (no image)', 'use_anisotropic': True, 'image': None},
    ]
    
    results = []
    
    for kernel_config in kernel_types:
        print(f"Testing kernel: {kernel_config['name']}")
        
        reconstructed = run_mbsi(
            spot_adata,
            cell_coords=cell_coords,
            image=kernel_config['image'],
            use_anisotropic=kernel_config['use_anisotropic']
        )
        
        metrics = compute_all_metrics(true_adata, reconstructed)
        metrics['kernel_type'] = kernel_config['name']
        
        results.append(metrics)
    
    return pd.DataFrame(results)


def compare_ot_variants(
    spot_adata: ad.AnnData,
    true_adata: ad.AnnData,
    cell_coords: np.ndarray = None
) -> pd.DataFrame:
    """
    Compare balanced vs unbalanced OT.
    
    Parameters
    ----------
    spot_adata : AnnData
        Spot-level data
    true_adata : AnnData
        Ground truth
    cell_coords : ndarray, optional
        Cell coordinates
        
    Returns
    -------
    results : DataFrame
        Comparison of OT variants
    """
    ot_configs = [
        {'name': 'Unbalanced (rho=1)', 'rho1': 1.0, 'rho2': 1.0},
        {'name': 'Unbalanced (rho=0.5)', 'rho1': 0.5, 'rho2': 0.5},
        {'name': 'Unbalanced (rho=2)', 'rho1': 2.0, 'rho2': 2.0},
        {'name': 'Balanced', 'rho1': 1000, 'rho2': 1000},
    ]
    
    results = []
    
    for ot_config in ot_configs:
        print(f"Testing OT: {ot_config['name']}")
        
        reconstructed = run_mbsi(
            spot_adata,
            cell_coords=cell_coords,
            rho1=ot_config['rho1'],
            rho2=ot_config['rho2']
        )
        
        metrics = compute_all_metrics(true_adata, reconstructed)
        metrics['ot_variant'] = ot_config['name']
        
        results.append(metrics)
    
    return pd.DataFrame(results)
