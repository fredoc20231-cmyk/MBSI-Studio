"""
Data loaders for spatial transcriptomics data.

Supports:
- 10x Visium folder
- h5ad file
- CSV count matrix with spatial coordinates
- Optional H&E image
- Optional cell segmentation mask
"""

import os
from pathlib import Path
from typing import Optional, Union

import anndata as ad
import h5py
import numpy as np
import pandas as pd
import scanpy as sc
from scipy.io import mmread


def load_visium(path: Union[str, Path]) -> ad.AnnData:
    """
    Load 10x Visium data from a folder.
    
    Parameters
    ----------
    path : str or Path
        Path to Visium folder containing:
        - filtered_feature_bc_matrix.h5 or matrix.mtx
        - spatial/ folder with tissue_positions.csv
        
    Returns
    -------
    adata : AnnData
        AnnData object with spatial coordinates in obsm['spatial']
    """
    path = Path(path)
    
    # Try loading with scanpy first
    try:
        adata = sc.datasets.visium_sge(sample_id=str(path))
        return adata
    except Exception:
        pass
    
    # Manual loading
    # Load count matrix
    h5_path = path / "filtered_feature_bc_matrix.h5"
    mtx_path = path / "filtered_feature_bc_matrix" / "matrix.mtx"
    
    if h5_path.exists():
        with h5py.File(h5_path, 'r') as f:
            matrix = f['matrix']['data'][:]
            indices = f['matrix']['indices'][:]
            indptr = f['matrix']['indptr'][:]
            shape = f['matrix']['shape'][:]
            
        from scipy.sparse import csr_matrix
        X = csr_matrix((matrix, indices, indptr), shape=shape)
        
        # Get gene and barcode names
        genes = [g.decode() if isinstance(g, bytes) else g 
                 for g in f['matrix']['features']['name'][:]]
        barcodes = [b.decode() if isinstance(b, bytes) else b 
                    for b in f['matrix']['barcodes'][:]]
        
    elif mtx_path.exists():
        from scipy.sparse import csr_matrix
        X = csr_matrix(mmread(mtx_path).T)
        
        genes_path = path / "filtered_feature_bc_matrix" / "features.tsv"
        barcodes_path = path / "filtered_feature_bc_matrix" / "barcodes.tsv"
        
        genes = pd.read_csv(genes_path, sep='\t', header=None)[0].values
        barcodes = pd.read_csv(barcodes_path, sep='\t', header=None)[0].values
    else:
        raise FileNotFoundError(f"No count matrix found in {path}")
    
    # Load spatial coordinates
    spatial_path = path / "spatial" / "tissue_positions.csv"
    if not spatial_path.exists():
        spatial_path = path / "spatial" / "tissue_positions_list.csv"
    
    if spatial_path.exists():
        spatial_coords = pd.read_csv(spatial_path)
        # Extract x, y coordinates (columns vary by Visium version)
        if 'pxl_col_in_fullres' in spatial_coords.columns:
            coords = spatial_coords[['pxl_row_in_fullres', 'pxl_col_in_fullres']].values
        elif 'array_row' in spatial_coords.columns:
            coords = spatial_coords[['array_row', 'array_col']].values
        else:
            coords = spatial_coords.iloc[:, :2].values
    else:
        raise FileNotFoundError(f"No spatial coordinates found in {path}")
    
    # Create AnnData
    adata = ad.AnnData(X=X, dtype=np.float32)
    adata.var_names = genes
    adata.obs_names = barcodes
    adata.obsm['spatial'] = coords
    
    return adata


def load_h5ad(path: Union[str, Path]) -> ad.AnnData:
    """
    Load AnnData from h5ad file.
    
    Parameters
    ----------
    path : str or Path
        Path to h5ad file
        
    Returns
    -------
    adata : AnnData
        Loaded AnnData object
    """
    return ad.read_h5ad(path)


def load_counts_and_coords(
    counts_path: Union[str, Path],
    coords_path: Union[str, Path],
    counts_format: str = "csv"
) -> ad.AnnData:
    """
    Load count matrix and spatial coordinates from CSV files.
    
    Parameters
    ----------
    counts_path : str or Path
        Path to count matrix (genes x cells or cells x genes)
    coords_path : str or Path
        Path to spatial coordinates CSV (x, y columns)
    counts_format : str
        Format of count matrix: 'csv', 'tsv', or 'mtx'
        
    Returns
    -------
    adata : AnnData
        AnnData object with spatial coordinates
    """
    # Load counts
    if counts_format == "csv":
        counts = pd.read_csv(counts_path, index_col=0)
    elif counts_format == "tsv":
        counts = pd.read_csv(counts_path, sep='\t', index_col=0)
    elif counts_format == "mtx":
        from scipy.sparse import csr_matrix
        X = csr_matrix(mmread(counts_path).T)
        counts = pd.DataFrame.sparse.from_spmatrix(X)
    else:
        raise ValueError(f"Unknown counts format: {counts_format}")
    
    # Load coordinates
    coords = pd.read_csv(coords_path)
    
    # Ensure coordinates are in right order
    if len(coords) != counts.shape[0]:
        # Try transposing counts
        counts = counts.T
        if len(coords) != counts.shape[0]:
            raise ValueError(
                f"Coordinate count ({len(coords)}) doesn't match "
                f"count matrix dimensions {counts.shape}"
            )
    
    # Create AnnData
    adata = ad.AnnData(X=counts.values, dtype=np.float32)
    adata.var_names = counts.columns.astype(str).values
    adata.obs_names = counts.index.astype(str).values
    adata.obsm['spatial'] = coords[['x', 'y']].values if 'x' in coords.columns else coords.iloc[:, :2].values
    
    return adata


def load_image(image_path: Union[str, Path]) -> np.ndarray:
    """
    Load tissue image (H&E or other).
    
    Parameters
    ----------
    image_path : str or Path
        Path to image file
        
    Returns
    -------
    image : ndarray
        Image array (H x W x C)
    """
    from PIL import Image
    
    image = Image.open(image_path)
    return np.array(image)


def load_segmentation(mask_path: Union[str, Path]) -> np.ndarray:
    """
    Load cell segmentation mask.
    
    Parameters
    ----------
    mask_path : str or Path
        Path to segmentation mask
        
    Returns
    -------
    mask : ndarray
        Segmentation mask (H x W) with cell IDs
    """
    from PIL import Image
    
    mask = Image.open(mask_path)
    return np.array(mask)
