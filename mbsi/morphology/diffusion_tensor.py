"""
Diffusion tensor estimation from morphology features.

Estimates anisotropic diffusion tensors that capture tissue structure
for use in the diffusion kernel.
"""

from typing import Optional, Tuple

import numpy as np
from scipy import ndimage


def estimate_diffusion_tensor(
    features: np.ndarray,
    anisotropy_strength: float = 1.0,
    min_eigenvalue: float = 0.1
) -> np.ndarray:
    """
    Estimate diffusion tensor from morphology features.
    
    Parameters
    ----------
    features : ndarray
        Feature array (H x W x n_features)
    anisotropy_strength : float
        Strength of anisotropy (0 = isotropic, higher = more anisotropic)
    min_eigenvalue : float
        Minimum eigenvalue for numerical stability
        
    Returns
    -------
    tensors : ndarray
        Diffusion tensor field (H x W x 2 x 2)
        Each 2x2 tensor is symmetric positive definite
    """
    H, W, n_features = features.shape
    
    # Compute structure tensor from gradient features
    # Use first two features as gradient components
    grad_x = features[..., 0] if n_features > 0 else np.zeros((H, W))
    grad_y = features[..., 1] if n_features > 1 else np.zeros((H, W))
    
    # Compute structure tensor components
    # J = [grad_x^2, grad_x*grad_y; grad_x*grad_y, grad_y^2]
    J_xx = grad_x**2
    J_xy = grad_x * grad_y
    J_yy = grad_y**2
    
    # Smooth structure tensor
    sigma = 2.0
    J_xx = ndimage.gaussian_filter(J_xx, sigma=sigma)
    J_xy = ndimage.gaussian_filter(J_xy, sigma=sigma)
    J_yy = ndimage.gaussian_filter(J_yy, sigma=sigma)
    
    # Compute eigenvalues and eigenvectors
    tensors = np.zeros((H, W, 2, 2))
    
    for i in range(H):
        for j in range(W):
            # Structure tensor at this pixel
            J = np.array([[J_xx[i, j], J_xy[i, j]],
                         [J_xy[i, j], J_yy[i, j]]])
            
            # Eigen decomposition
            eigvals, eigvecs = np.linalg.eigh(J)
            
            # Ensure positive eigenvalues
            eigvals = np.maximum(eigvals, min_eigenvalue)
            
            # Create diffusion tensor
            # Diffusion is stronger perpendicular to gradient direction
            # (along tissue structure)
            D = eigvecs @ np.diag(eigvals) @ eigvecs.T
            
            # Apply anisotropy strength
            D = D ** anisotropy_strength
            
            # Ensure positive definite
            D = (D + D.T) / 2
            D = D + min_eigenvalue * np.eye(2)
            
            tensors[i, j] = D
    
    return tensors


def build_tensor_field(
    coords: np.ndarray,
    image: Optional[np.ndarray] = None,
    anisotropy_strength: float = 1.0,
    isotropic: bool = False
) -> np.ndarray:
    """
    Build diffusion tensor field for given coordinates.
    
    Parameters
    ----------
    coords : ndarray
        Spatial coordinates (n x 2)
    image : ndarray, optional
        Tissue image (H x W x C). If None, uses isotropic tensors.
    anisotropy_strength : float
        Strength of anisotropy
    isotropic : bool
        If True, force isotropic diffusion regardless of image
        
    Returns
    -------
    tensor_field : ndarray
        Diffusion tensor at each coordinate (n x 2 x 2)
    """
    n_points = coords.shape[0]
    
    if isotropic or image is None:
        # Isotropic diffusion (identity tensor)
        tensor_field = np.tile(np.eye(2)[np.newaxis, :, :], (n_points, 1, 1))
        return tensor_field
    
    # Compute features from image
    from mbsi.morphology.image_features import compute_morphology_features
    features = compute_morphology_features(image)
    
    # Estimate tensor field from image
    tensors = estimate_diffusion_tensor(features, anisotropy_strength)
    
    # Interpolate tensors to coordinate locations
    H, W = features.shape[:2]
    tensor_field = np.zeros((n_points, 2, 2))
    
    for i in range(n_points):
        x, y = coords[i]
        
        # Map to image coordinates
        ix = int(np.clip(x / W * W, 0, W - 1))
        iy = int(np.clip(y / H * H, 0, H - 1))
        
        tensor_field[i] = tensors[iy, ix]
    
    return tensor_field


def tensor_distance(
    x1: np.ndarray,
    x2: np.ndarray,
    tensor: np.ndarray
) -> float:
    """
    Compute Mahalanobis distance using diffusion tensor.
    
    Parameters
    ----------
    x1, x2 : ndarray
        Points (2,)
    tensor : ndarray
        Diffusion tensor (2 x 2)
        
    Returns
    -------
    distance : float
        Mahalanobis distance: sqrt((x1-x2)^T @ tensor @ (x1-x2))
    """
    diff = x1 - x2
    inv_tensor = np.linalg.inv(tensor)
    distance = np.sqrt(diff @ inv_tensor @ diff)
    return distance
