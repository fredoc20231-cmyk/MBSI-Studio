"""Segmentation quality control metrics and warnings."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd
from skimage import measure


def _cell_areas(label_mask: np.ndarray) -> np.ndarray:
    props = measure.regionprops(label_mask.astype(np.int32))
    return np.array([p.area for p in props], dtype=float) if props else np.array([])


def compute_label_mask_qc(
    label_mask: np.ndarray,
    image: Optional[np.ndarray] = None,
    transcript_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Compute QC metrics for a 2D label mask (Milestone 1 API)."""
    label_mask = np.asarray(label_mask)
    warnings: list[str] = []
    areas = _cell_areas(label_mask) if label_mask.ndim >= 2 else np.array([])

    n_cells = int(len(areas))
    tissue_coverage = 0.0
    if label_mask.ndim >= 2 and label_mask.size:
        tissue_coverage = round(100.0 * np.sum(label_mask > 0) / label_mask.size, 2)

    percent_transcripts_assigned = None
    if transcript_df is not None and len(transcript_df):
        x_col = next((c for c in ("x", "x_location", "vertex_x") if c in transcript_df.columns), None)
        y_col = next((c for c in ("y", "y_location", "vertex_y") if c in transcript_df.columns), None)
        if x_col and y_col and label_mask.ndim >= 2:
            h, w = label_mask.shape[:2]
            xs = pd.to_numeric(transcript_df[x_col], errors="coerce").fillna(-1).astype(int)
            ys = pd.to_numeric(transcript_df[y_col], errors="coerce").fillna(-1).astype(int)
            assigned = 0
            for x, y in zip(xs, ys):
                if 0 <= x < w and 0 <= y < h and int(label_mask[y, x]) > 0:
                    assigned += 1
            percent_transcripts_assigned = round(
                100.0 * assigned / max(len(transcript_df), 1),
                2,
            )
        else:
            warnings.append("transcript table missing x/y columns for assignment QC")

    if n_cells == 0:
        warnings.append("no cells detected in label mask")
    if tissue_coverage < 5:
        warnings.append("low tissue coverage")
    if areas.size and float(np.median(areas)) < 5:
        warnings.append("extreme cell sizes (very small)")

    result: Dict[str, Any] = {
        "n_cells": n_cells,
        "median_cell_area": float(np.median(areas)) if areas.size else 0.0,
        "mean_cell_area": float(np.mean(areas)) if areas.size else 0.0,
        "area_iqr": float(np.percentile(areas, 75) - np.percentile(areas, 25)) if areas.size else 0.0,
        "tissue_coverage": tissue_coverage,
        "percent_transcripts_assigned": percent_transcripts_assigned,
        "warnings": warnings,
        "qc_pass": len(warnings) == 0 or n_cells > 0,
    }
    if image is not None:
        result["image_shape"] = list(image.shape)
    return result


def compute_segmentation_qc(
    adata: Any = None,
    tissue_mask: Optional[np.ndarray] = None,
    nuclei_mask: Optional[np.ndarray] = None,
    cell_mask: Optional[np.ndarray] = None,
    boundary_map: Optional[np.ndarray] = None,
    registration: Optional[Dict[str, Any]] = None,
    image: Optional[np.ndarray] = None,
    label_mask: Optional[np.ndarray] = None,
    transcript_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Compute segmentation QC metrics and warnings."""
    mask_for_qc = label_mask if label_mask is not None else cell_mask
    if mask_for_qc is not None and mask_for_qc.ndim >= 2 and adata is None and tissue_mask is None:
        return compute_label_mask_qc(mask_for_qc, image=image, transcript_df=transcript_df)

    metrics: Dict[str, Any] = {}
    warnings: list[str] = []

    if image is None and tissue_mask is None and cell_mask is None and label_mask is None:
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

    effective_mask = mask_for_qc
    if effective_mask is not None:
        if effective_mask.ndim == 1:
            n_cells = int(np.sum(effective_mask >= 0))
            areas = np.ones(n_cells)
        else:
            areas = _cell_areas(effective_mask)
            n_cells = len(areas)
        metrics["cell_count"] = n_cells
        metrics["n_cells"] = n_cells
        if len(areas):
            metrics["median_cell_area"] = float(np.median(areas))
            metrics["mean_cell_area"] = float(np.mean(areas))
            metrics["area_iqr"] = float(np.percentile(areas, 75) - np.percentile(areas, 25))
            metrics["cell_area_p95"] = float(np.percentile(areas, 95))
            metrics["tissue_coverage"] = round(
                100.0 * np.sum(effective_mask > 0) / max(effective_mask.size, 1),
                2,
            )
            if metrics["median_cell_area"] < 5:
                warnings.append("extreme cell sizes (very small)")
            if metrics.get("cell_area_p95", 0) > 1e5:
                warnings.append("extreme cell sizes (very large)")

    if transcript_df is not None and effective_mask is not None and effective_mask.ndim >= 2:
        label_qc = compute_label_mask_qc(effective_mask, transcript_df=transcript_df)
        metrics["percent_transcripts_assigned"] = label_qc.get("percent_transcripts_assigned")
        warnings.extend(label_qc.get("warnings", []))

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

    has_seg = any(x is not None for x in (tissue_mask, nuclei_mask, cell_mask, label_mask))
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
