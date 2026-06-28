"""
File upload components for the UI.
"""

import streamlit as st
import anndata as ad
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import zipfile


def h5ad_uploader() -> Optional[ad.AnnData]:
    """
    Upload and validate h5ad file.
    
    Returns
    -------
    adata : AnnData or None
        Loaded AnnData object
    """
    uploaded_file = st.file_uploader(
        "Upload h5ad file",
        type=['h5ad'],
        key="h5ad_uploader"
    )
    
    if uploaded_file is not None:
        try:
            # Save to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.h5ad') as f:
                f.write(uploaded_file.getbuffer())
                temp_path = f.name
            
            adata = ad.read_h5ad(temp_path)
            
            # Validation
            if 'spatial' not in adata.obsm:
                st.warning("No spatial coordinates found in obsm['spatial']")
            
            st.success(f"Loaded: {adata.n_obs} spots, {adata.n_vars} genes")
            return adata
            
        except Exception as e:
            st.error(f"Error loading h5ad file: {str(e)}")
            return None
    
    return None


def csv_matrix_uploader() -> Optional[pd.DataFrame]:
    """
    Upload count matrix CSV.
    
    Returns
    -------
    df : DataFrame or None
        Loaded count matrix
    """
    uploaded_file = st.file_uploader(
        "Upload count matrix CSV",
        type=['csv'],
        key="csv_matrix_uploader"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, index_col=0)
            st.success(f"Loaded: {df.shape[0]} cells, {df.shape[1]} genes")
            return df
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
            return None
    
    return None


def coordinates_uploader() -> Optional[pd.DataFrame]:
    """
    Upload spatial coordinates CSV.
    
    Returns
    -------
    df : DataFrame or None
        Loaded coordinates
    """
    uploaded_file = st.file_uploader(
        "Upload spatial coordinates CSV (x, y columns)",
        type=['csv'],
        key="coords_uploader"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            if 'x' not in df.columns or 'y' not in df.columns:
                st.error("CSV must contain 'x' and 'y' columns")
                return None
            
            st.success(f"Loaded {len(df)} coordinate pairs")
            return df
        except Exception as e:
            st.error(f"Error loading coordinates: {str(e)}")
            return None
    
    return None


def image_uploader() -> Optional[np.ndarray]:
    """
    Upload image file (PNG, JPG, TIF).
    
    Returns
    -------
    image : ndarray or None
        Loaded image
    """
    uploaded_file = st.file_uploader(
        "Upload tissue image",
        type=['png', 'jpg', 'jpeg', 'tif', 'tiff'],
        key="image_uploader"
    )
    
    if uploaded_file is not None:
        try:
            from PIL import Image
            image = Image.open(uploaded_file)
            image_array = np.array(image)
            st.success(f"Loaded image: {image_array.shape}")
            return image_array
        except Exception as e:
            st.error(f"Error loading image: {str(e)}")
            return None
    
    return None


def segmentation_uploader() -> Optional[np.ndarray]:
    """
    Upload segmentation mask.
    
    Returns
    -------
    mask : ndarray or None
        Loaded segmentation mask
    """
    uploaded_file = st.file_uploader(
        "Upload segmentation mask",
        type=['png', 'tif', 'tiff'],
        key="segmentation_uploader"
    )
    
    if uploaded_file is not None:
        try:
            from PIL import Image
            mask = Image.open(uploaded_file)
            mask_array = np.array(mask)
            st.success(f"Loaded mask: {mask_array.shape}")
            return mask_array
        except Exception as e:
            st.error(f"Error loading mask: {str(e)}")
            return None
    
    return None


def visium_folder_uploader() -> Optional[dict]:
    """
    Upload Visium folder as ZIP.
    
    Returns
    -------
    files : dict or None
        Dictionary of extracted files
    """
    uploaded_file = st.file_uploader(
        "Upload Visium folder as ZIP",
        type=['zip'],
        key="visium_uploader"
    )
    
    if uploaded_file is not None:
        try:
            import tempfile
            import os
            
            # Extract ZIP with zip-slip protection
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        member_path = Path(temp_dir) / member
                        if not str(member_path.resolve()).startswith(
                            str(Path(temp_dir).resolve())
                        ):
                            st.error("Rejected: ZIP contains path traversal entries")
                            return None
                    zip_ref.extractall(temp_dir)
                
                # Look for Visium files
                files = {}
                for file in Path(temp_dir).rglob('*'):
                    if file.is_file():
                        files[file.name] = str(file)
                
                if len(files) > 0:
                    st.success(f"Extracted {len(files)} files")
                    return files
                else:
                    st.error("No files found in ZIP")
                    return None
                    
        except Exception as e:
            st.error(f"Error extracting ZIP: {str(e)}")
            return None
    
    return None


def data_readiness_score(adata) -> Tuple[int, str]:
    """
    Compute data readiness score.
    
    Parameters
    ----------
    adata : AnnData
        AnnData object to check
        
    Returns
    -------
    score : int
        Readiness score (0-100)
    status : str
        Readiness status
    """
    score = 0
    issues = []
    
    if adata is None:
        return 0, "No data loaded"
    
    # Check spatial coordinates
    if 'spatial' in adata.obsm:
        score += 40
    else:
        issues.append("Missing spatial coordinates")
    
    # Check expression matrix
    if adata.X is not None and adata.X.sum() > 0:
        score += 30
    else:
        issues.append("Empty expression matrix")
    
    # Check gene names
    if len(adata.var_names) > 0:
        score += 15
    else:
        issues.append("No gene names")
    
    # Check for missing values
    if hasattr(adata.X, 'toarray'):
        X = adata.X.toarray()
    else:
        X = adata.X
    
    if not np.isnan(X).any():
        score += 15
    else:
        issues.append("Contains missing values")
    
    # Determine status
    if score >= 90:
        status = "Ready for reconstruction"
    elif score >= 70:
        status = "Ready for validation"
    elif score >= 50:
        status = "Missing optional data"
    else:
        status = "Missing required data"
    
    return score, status


def upload_panel() -> dict:
    """
    Complete upload panel with all file types.
    
    Returns
    -------
    data : dict
        Dictionary of uploaded data
    """
    st.subheader("Data Upload")
    
    data = {}
    
    # File type tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "h5ad", "CSV Matrix", "Coordinates", "Image", "Segmentation"
    ])
    
    with tab1:
        data['adata'] = h5ad_uploader()
    
    with tab2:
        data['count_matrix'] = csv_matrix_uploader()
    
    with tab3:
        data['coordinates'] = coordinates_uploader()
    
    with tab4:
        data['image'] = image_uploader()
    
    with tab5:
        data['segmentation'] = segmentation_uploader()
    
    # Data readiness check
    if 'adata' in data and data['adata'] is not None:
        score, status = data_readiness_score(data['adata'])
        
        st.markdown("---")
        st.subheader("Data Readiness")
        
        col1, col2 = st.columns(2)
        col1.metric("Readiness Score", f"{score}/100")
        col2.metric("Status", status)
    
    return data
