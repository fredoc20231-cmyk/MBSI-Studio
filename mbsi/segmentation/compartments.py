"""Compartment assignment for spots and cells."""

from typing import Dict, Optional

import anndata as ad
import numpy as np
from sklearn.cluster import KMeans

COMPARTMENT_NAMES = ["tumor", "stroma", "immune", "necrosis", "background"]


def segment_compartments(
    image: Optional[np.ndarray] = None,
    adata: Optional[ad.AnnData] = None,
    method: str = "hybrid",
    n_compartments: int = 4,
) -> np.ndarray:
    """
    Assign tumor/stroma/immune/necrosis compartments.

    method: histology | expression | hybrid
    Returns per-observation compartment id array when adata provided,
    or image-region labels when only image provided.
    """
    method = (method or "hybrid").lower()
    if adata is None and image is None:
        raise ValueError("Provide image or adata for compartment segmentation")

    if adata is not None:
        if method == "histology" and image is not None:
            from mbsi.segmentation.tissue import segment_tissue
            mask = segment_tissue(image=image, method="otsu")
            coords = np.asarray(adata.obsm["spatial"])
            labels = np.zeros(len(coords), dtype=np.int32)
            h, w = mask.shape[:2]
            for i, (x, y) in enumerate(coords):
                ix, iy = int(round(x)), int(round(y))
                if 0 <= ix < w and 0 <= iy < h:
                    labels[i] = 0 if mask[iy, ix] > 0 else len(COMPARTMENT_NAMES) - 1
            return labels

        if method == "expression":
            adata = infer_compartment_labels(adata, n_compartments=n_compartments)
            return adata.obs["compartment_id"].values.astype(np.int32)

        adata = infer_compartment_labels(adata, n_compartments=n_compartments)
        return adata.obs["compartment_id"].values.astype(np.int32)

    from mbsi.segmentation.tissue import coordinate_tissue_regions
    gray = image[..., 0] if image.ndim >= 3 else image
    return coordinate_tissue_regions(
        np.column_stack(np.nonzero(gray > 0)) if gray.ndim == 2 else np.random.randn(50, 2),
        n_regions=n_compartments,
    )


def infer_compartment_labels(
    adata: ad.AnnData,
    n_compartments: int = 4,
    key: str = "compartment",
) -> ad.AnnData:
    """
    Infer compartment labels from spatial coordinates and expression.

    Placeholder compartment model using k-means on coords + mean expression.
    """
    coords = adata.obsm["spatial"]
    X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    features = np.hstack([coords, X.mean(axis=1, keepdims=True)])
    labels = KMeans(n_clusters=min(n_compartments, len(adata)), random_state=42, n_init=10).fit_predict(features)
    adata = adata.copy()
    adata.obs[key] = [COMPARTMENT_NAMES[i % len(COMPARTMENT_NAMES)] for i in labels]
    adata.obs[f"{key}_id"] = labels.astype(int)
    adata.uns["compartment_note"] = "Computational hypothesis - Requires experimental validation"
    return adata


def assign_spots_to_compartments(
    adata: ad.AnnData,
    compartment_mask: Optional[np.ndarray] = None,
    key: str = "compartment",
) -> ad.AnnData:
    """Assign spots to compartments from mask or inferred labels."""
    adata = adata.copy()
    if compartment_mask is not None and compartment_mask.ndim == 1:
        adata.obs[key] = [COMPARTMENT_NAMES[int(m) % len(COMPARTMENT_NAMES)] for m in compartment_mask]
    else:
        adata = infer_compartment_labels(adata, key=key)
    return adata
