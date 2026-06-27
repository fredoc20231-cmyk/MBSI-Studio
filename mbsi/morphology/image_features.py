"""
Image feature extraction for tissue morphology.

Extracts features from H&E images or other tissue images to inform
diffusion tensor estimation.
"""

from typing import Optional, Tuple

import numpy as np
from scipy import ndimage
from skimage import feature, filters, segmentation


def compute_morphology_features(
    image: np.ndarray,
    sigma: float = 2.0
) -> np.ndarray:
    """
    Compute morphology features from tissue image.
    
    Parameters
    ----------
    image : ndarray
        Image array (H x W x C) or grayscale (H x W)
    sigma : float
        Gaussian smoothing sigma for feature computation
        
    Returns
    -------
    features : ndarray
        Feature array (H x W x n_features)
        Features include:
        - Gradient magnitude
        - Gradient direction
        - Texture (local binary pattern)
        - Intensity
    """
    # Convert to grayscale if needed
    if image.ndim == 3:
        if image.shape[2] == 3:  # RGB
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        elif image.shape[2] == 4:  # RGBA
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image[..., 0]
    else:
        gray = image
    
    # Smooth image
    smoothed = filters.gaussian(gray, sigma=sigma)
    
    # Compute gradient
    grad_y, grad_x = np.gradient(smoothed)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    grad_dir = np.arctan2(grad_y, grad_x)
    
    # Compute texture features using local binary patterns
    lbp = feature.local_binary_pattern(
        gray.astype(np.uint8),
        P=8,
        R=1,
        method='uniform'
    )
    
    # Stack features
    features = np.stack([
        grad_mag,
        np.cos(grad_dir),
        np.sin(grad_dir),
        lbp / lbp.max(),
        smoothed / smoothed.max()
    ], axis=-1)
    
    return features


def compute_tissue_mask(
    image: np.ndarray,
    threshold: Optional[float] = None
) -> np.ndarray:
    """
    Compute tissue mask from image.
    
    Parameters
    ----------
    image : ndarray
        Image array (H x W x C) or grayscale (H x W)
    threshold : float, optional
        Threshold for tissue detection. If None, use Otsu's method.
        
    Returns
    -------
    mask : ndarray
        Binary tissue mask (H x W)
    """
    # Convert to grayscale
    if image.ndim == 3:
        if image.shape[2] == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image[..., 0]
    else:
        gray = image
    
    # Apply threshold
    if threshold is None:
        threshold = filters.threshold_otsu(gray)
    
    mask = gray > threshold
    
    # Clean up mask
    mask = ndimage.binary_closing(mask, structure=np.ones((3, 3)))
    mask = ndimage.binary_fill_holes(mask)
    
    return mask.astype(np.uint8)


def detect_boundaries(
    image: np.ndarray,
    sigma: float = 1.0
) -> np.ndarray:
    """
    Detect tissue boundaries using edge detection.
    
    Parameters
    ----------
    image : ndarray
        Image array
    sigma : float
        Gaussian smoothing sigma
        
    Returns
    -------
    boundaries : ndarray
        Boundary probability map (H x W)
    """
    # Convert to grayscale
    if image.ndim == 3:
        if image.shape[2] == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image[..., 0]
    else:
        gray = image
    
    # Compute edges
    edges = feature.canny(gray, sigma=sigma)
    
    # Distance transform for soft boundaries
    distance = ndimage.distance_transform_edt(~edges)
    distance = distance / distance.max()
    
    # Invert so edges have high values
    boundaries = 1 - distance
    
    return boundaries
