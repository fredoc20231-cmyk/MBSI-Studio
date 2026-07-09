"""Optional segmentation backends with graceful fallbacks."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
from skimage.filters import threshold_local, threshold_otsu
from skimage.morphology import remove_small_objects

from mbsi.morphology.image_features import compute_tissue_mask
from mbsi.morphology.segmentation import segment_cells as _watershed_cells


def _to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3:
        return np.dot(image[..., :3], [0.299, 0.587, 0.114]).astype(np.float64)
    return image.astype(np.float64)


def cellpose_available() -> bool:
    try:
        import cellpose  # noqa: F401
        return True
    except ImportError:
        return False


def stardist_available() -> bool:
    try:
        import stardist  # noqa: F401
        return True
    except ImportError:
        return False


def sam_available() -> bool:
    try:
        import segment_anything  # noqa: F401
        return True
    except ImportError:
        return False


def mesmer_available() -> bool:
    from mbsi.segmentation.deepcell_mesmer_pipeline import mesmer_available as _mesmer_available

    return _mesmer_available()


def baseline_unet_available() -> bool:
    from mbsi.segmentation.baseline_unet import baseline_unet_weights_available

    return baseline_unet_weights_available()


def available_backends() -> Dict[str, bool]:
    return {
        "cellpose": cellpose_available(),
        "stardist": stardist_available(),
        "mesmer": mesmer_available(),
        "baseline_unet": baseline_unet_available(),
        "sam": sam_available(),
        "otsu": True,
        "adaptive": True,
        "watershed": True,
        "voronoi": True,
    }


def segment_tissue_otsu(image: np.ndarray, min_size: int = 100) -> np.ndarray:
    mask = compute_tissue_mask(image)
    mask = remove_small_objects(mask.astype(bool), min_size=min_size)
    return mask.astype(np.uint8)


def segment_tissue_adaptive(image: np.ndarray, block_size: int = 51, min_size: int = 100) -> np.ndarray:
    gray = _to_gray(image)
    gray = (gray - gray.min()) / (gray.max() - gray.min() + 1e-10)
    block = max(3, block_size | 1)
    thresh = threshold_local(gray, block_size=block)
    mask = gray > thresh
    mask = remove_small_objects(mask, min_size=min_size)
    return mask.astype(np.uint8)


def segment_tissue_sam(image: np.ndarray) -> Optional[np.ndarray]:
    if not sam_available():
        return None
    try:
        from segment_anything import SamAutomaticMaskGenerator, sam_model_registry
        gray = _to_gray(image)
        rgb = np.stack([gray, gray, gray], axis=-1)
        rgb = ((rgb - gray.min()) / (gray.max() - gray.min() + 1e-10) * 255).astype(np.uint8)
        model = sam_model_registry["vit_b"](checkpoint=None)
        generator = SamAutomaticMaskGenerator(model)
        masks = generator.generate(rgb)
        if not masks:
            return None
        combined = np.zeros(image.shape[:2], dtype=bool)
        for item in masks:
            combined |= item["segmentation"]
        return combined.astype(np.uint8)
    except Exception:
        return None


def segment_nuclei_cellpose(image: np.ndarray) -> Optional[np.ndarray]:
    if not cellpose_available():
        return None
    try:
        from cellpose import models
        model = models.Cellpose(model_type="nuclei", gpu=False)
        gray = _to_gray(image)
        masks, _, _, _ = model.eval(gray, diameter=None, channels=[0, 0])
        return masks.astype(np.int32)
    except Exception:
        return None


def segment_nuclei_stardist(image: np.ndarray) -> Optional[np.ndarray]:
    if not stardist_available():
        return None
    try:
        from csbdeep.utils import normalize
        from stardist.models import StarDist2D
        model = StarDist2D.from_pretrained("2D_versatile_fluo")
        gray = normalize(_to_gray(image))
        labels, _ = model.predict_instances(gray)
        return labels.astype(np.int32)
    except Exception:
        return None


def segment_nuclei_watershed(image: np.ndarray, min_size: int = 30) -> np.ndarray:
    return segment_cells_watershed(image, min_size=min_size)


def segment_cells_watershed(image: np.ndarray, min_size: int = 50) -> np.ndarray:
    return _watershed_cells(image, min_size=min_size, method="watershed")


def get_technology_segmentation_plan(technology_key: str) -> Dict[str, Any]:
    """Technology-specific segmentation guidance for workspace UI."""
    plans = {
        "visium": {
            "tissue": ["otsu", "adaptive", "sam"],
            "cells": ["voronoi"],
            "registration": ["scalefactors", "affine"],
            "notes": "H&E tissue mask and spot registration; pseudo-cell via Voronoi if no segmentation.",
        },
        "visium_hd": {
            "tissue": ["otsu", "adaptive", "sam"],
            "cells": ["cellpose", "stardist", "voronoi"],
            "registration": ["scalefactors", "affine"],
            "notes": "Visium HD H&E tissue mask with bin/spot registration.",
        },
        "xenium": {
            "tissue": ["imported", "otsu"],
            "cells": ["imported", "stardist", "cellpose", "mesmer", "watershed", "voronoi"],
            "registration": ["morphology", "affine"],
            "notes": "Import cell boundaries GeoJSON/CSV/parquet; StarDist/Cellpose/Mesmer on morphology when needed.",
        },
        "merfish": {
            "tissue": ["otsu", "adaptive"],
            "cells": ["imported", "voronoi"],
            "registration": ["affine"],
            "notes": "Use cell metadata and boundary files when available.",
        },
        "cosmx": {
            "tissue": ["otsu", "adaptive"],
            "cells": ["imported", "cellpose"],
            "registration": ["fov_offsets", "affine"],
            "notes": "FOV morphology images and stitched cell boundaries.",
        },
        "stereo_seq": {
            "tissue": ["imported", "otsu"],
            "cells": ["imported", "voronoi"],
            "registration": ["gef_coords", "affine"],
            "notes": "Bin/cell/region from SAW/StereoMap; lasso regions supported.",
        },
        "codex": {
            "tissue": ["otsu", "adaptive"],
            "cells": ["cellpose", "stardist", "watershed"],
            "registration": ["affine"],
            "notes": "Multiplex IF nuclei/cell segmentation.",
        },
    }
    return plans.get(
        technology_key,
        {
            "tissue": ["otsu", "adaptive"],
            "cells": ["watershed", "voronoi", "imported"],
            "registration": ["affine"],
            "notes": "Generic affine registration and Otsu tissue mask fallback.",
        },
    )
