"""
Cell segmentation utilities.

Provides functions for working with cell segmentation masks
and extracting cell-level information.
"""

from typing import Optional, Tuple

import numpy as np
from scipy import ndimage
from skimage import measure, morphology


def segment_cells(
    image: np.ndarray,
    min_size: int = 50,
    method: str = "watershed"
) -> np.ndarray:
    """
    Segment cells from tissue image.
    
    Parameters
    ----------
    image : ndarray
        Tissue image (H x W x C) or grayscale (H x W)
    min_size : int
        Minimum cell size in pixels
    method : str
        Segmentation method: 'watershed' or 'threshold'
        
    Returns
    -------
    labels : ndarray
        Cell segmentation mask (H x W) with cell IDs
    """
    # Convert to grayscale
    if image.ndim == 3:
        if image.shape[2] == 3:
            gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        else:
            gray = image[..., 0]
    else:
        gray = image
    
    # Normalize
    gray = (gray - gray.min()) / (gray.max() - gray.min())
    
    if method == "watershed":
        # Watershed segmentation
        from skimage.filters import sobel
        from skimage.segmentation import watershed
        
        # Compute elevation map
        elevation = sobel(gray)
        
        # Find markers
        markers = np.zeros_like(gray, dtype=np.int32)
        markers[gray < 0.3] = 1
        markers[gray > 0.7] = 2
        
        # Watershed
        labels = watershed(elevation, markers)
        
    elif method == "threshold":
        # Threshold-based segmentation
        from skimage.filters import threshold_otsu
        
        thresh = threshold_otsu(gray)
        binary = gray > thresh
        
        # Remove small objects
        binary = morphology.remove_small_objects(binary, min_size=min_size)
        
        # Label
        labels = measure.label(binary)
        
    else:
        raise ValueError(f"Unknown segmentation method: {method}")
    
    return labels


def get_cell_centroids(labels: np.ndarray) -> np.ndarray:
    """
    Get centroid coordinates for each cell in segmentation mask.
    
    Parameters
    ----------
    labels : ndarray
        Segmentation mask (H x W)
        
    Returns
    -------
    centroids : ndarray
        Centroid coordinates (n_cells x 2) as (y, x)
    """
    regions = measure.regionprops(labels)
    centroids = np.array([r.centroid for r in regions])
    return centroids


def overlay_segmentation(
    image: np.ndarray,
    labels: np.ndarray,
    alpha: float = 0.3
) -> np.ndarray:
    """
    Overlay segmentation mask on image.
    
    Parameters
    ----------
    image : ndarray
        Original image (H x W x C)
    labels : ndarray
        Segmentation mask (H x W)
    alpha : float
        Transparency of overlay
        
    Returns
    -------
    overlay : ndarray
        Image with segmentation overlay (H x W x C)
    """
    # Convert to RGB if needed
    if image.ndim == 2:
        image = np.stack([image] * 3, axis=-1)
    
    # Colorize labels
    from skimage import color
    colored_labels = color.label2rgb(labels, image=image, alpha=alpha)
    
    return colored_labels


def refine_segmentation(
    labels: np.ndarray,
    min_size: int = 50,
    max_size: Optional[int] = None
) -> np.ndarray:
    """
    Refine segmentation by removing small/large objects.
    
    Parameters
    ----------
    labels : ndarray
        Segmentation mask (H x W)
    min_size : int
        Minimum object size
    max_size : int, optional
        Maximum object size
        
    Returns
    -------
    refined : ndarray
        Refined segmentation mask
    """
    # Remove small objects
    refined = morphology.remove_small_objects(labels, min_size=min_size)
    
    # Remove large objects if specified
    if max_size is not None:
        refined = morphology.remove_small_objects(
            refined > 0,
            min_size=max_size
        )
        refined = measure.label(refined)
    
    return refined
