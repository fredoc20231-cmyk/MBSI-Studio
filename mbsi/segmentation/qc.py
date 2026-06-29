"""Segmentation quality control metrics and warnings."""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
from skimage import measure


def compute_segmentation_qc(
    adata: Any = None,
    tissue_mask: Optional[np.ndarray] = None,
    nuclei_mask: Optional[np.ndarray] = None,
    cell_mask: Optional[np.ndarray] = None,
    boundary_map: Optional[np.ndarray] = None,
    registration: Optional[Dict[str, Any]] = None,
    image: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Compute segmentation QC metrics and warnings."""
    metrics: Dict[str, Any] = {}
    warnings: list[str] = []

    if image is None and tissue_mask is None and cell_mask is None:
        warnings.append("no image or segmentation outputs")

    if tissue_mask is not None and tissue_mask.ndim >= 2:
        tissue_area = int(np.sum(tissue_mask > 0))
        total_area = int(tissue_mask.size)
        metrics["tissue_area_pixels"] = tissue_area
        metrics["percent_tissue_covered"] = round(100.0 * tissue_area / max(total_area, 1), 2)
        if metrics["percent_tissue_covered"] < 5:
            warnings.append("low tissue coverage")

    if nuclei_mask is not None and nuclei_mask.ndim >= 2:
        n_nuclei = int(nuclei_mask.max())
        metrics["nuclei_count"] = n_nuclei
        if n_nuclei == 0:
            warnings.append("no nuclei detected")

    if cell_mask is not None:
        if cell_mask.ndim == 1:
            n_cells = int(np.sum(cell_mask >= 0))
            areas = np.ones(n_cells)
        else:
            props = measure.regionprops(cell_mask.astype(np.int32))
            areas = np.array([p.area for p in props]) if props else np.array([])
            n_cells = len(props)
        metrics["cell_count"] = n_cells
        if len(areas):
            metrics["median_cell_area"] = float(np.median(areas))
            metrics["cell_area_p95"] = float(np.percentile(areas, 95))
            if metrics["median_cell_area"] < 5:
                warnings.append("extreme cell sizes (very small)")
            if metrics["cell_area_p95"] > 1e5:
                warnings.append("extreme cell sizes (very large)")

    if adata is not None and tissue_mask is not None and tissue_mask.ndim >= 2:
        coords_key = "spatial_registered" if "spatial_registered" in adata.obsm else "spatial"
        coords = np.asarray(adata.obsm[coords_key])
        h, w = tissue_mask.shape[:2]
        inside = 0
        outside = 0
        for x, y in coords:
            ix, iy = int(round(x)), int(round(y))
            if 0 <= ix < w and 0 <= iy < h and tissue_mask[iy, ix] > 0:
                inside += 1
            else:
                outside += 1
        total = len(coords)
        metrics["percent_spots_inside_tissue"] = round(100.0 * inside / max(total, 1), 2)
        metrics["spots_outside_tissue"] = outside
        if outside > 0:
            warnings.append("cells/spots outside tissue")

    if boundary_map is not None and boundary_map.ndim >= 2:
        metrics["boundary_length_pixels"] = int(np.sum(boundary_map > 0))

    if registration:
        metrics["registration_valid"] = registration.get("valid", registration.get("status") == "ok")
        if registration.get("fraction_in_tissue", 1.0) < 0.5:
            warnings.append("registration mismatch")

    has_seg = any(
        x is not None
        for x in (tissue_mask, nuclei_mask, cell_mask)
    )
    if not has_seg:
        warnings.append("no segmentation mask detected")

    confidence = 100.0
    if warnings:
        confidence -= min(60.0, 15.0 * len(warnings))
    if metrics.get("percent_tissue_covered", 100) < 10:
        confidence -= 20
    metrics["segmentation_confidence"] = round(max(0.0, confidence), 1)
    metrics["qc_pass"] = len(warnings) == 0 or metrics["segmentation_confidence"] >= 50

    return {"metrics": metrics, "warnings": warnings, "qc_pass": metrics["qc_pass"]}
