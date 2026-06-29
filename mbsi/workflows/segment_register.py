"""Segmentation and registration workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from mbsi.discovery.segmentation_findings import build_segmentation_findings
from mbsi.schema.run import RunRecord
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WorkflowModule
from mbsi.segmentation import (
    attach_segmentation_to_adata,
    compute_segmentation_qc,
    detect_boundaries,
    export_segmentation_masks,
    register_spatial_to_image,
    segment_cells,
    segment_compartments,
    segment_nuclei,
    segment_tissue,
    validate_registration,
)
from mbsi.segmentation.adapters import get_technology_segmentation_plan
from mbsi.segmentation.cells import generate_voronoi_cells


def _synthetic_he_image(n: int = 128) -> np.ndarray:
    rng = np.random.default_rng(42)
    img = rng.integers(180, 240, (n, n, 3), dtype=np.uint8)
    img[20:100, 20:100] = rng.integers(80, 160, (80, 80, 3), dtype=np.uint8)
    return img


def run_segment_register_workflow(
    adata: Any,
    technology_key: str = "",
    image: Optional[np.ndarray] = None,
    tissue_method: str = "otsu",
    cell_method: str = "voronoi",
    compartment_method: str = "hybrid",
    segmentation_source: str = "run_tissue",
    imported_mask: Optional[np.ndarray] = None,
    out_dir: Optional[Path] = None,
) -> RunRecord:
    """Run full segmentation + registration pipeline."""
    if adata is None:
        return RunRecord.failed(WorkflowModule.SEGMENT_REGISTER.value, "no AnnData loaded")

    tech = get_technology(technology_key)
    plan = get_technology_segmentation_plan(technology_key)
    logic = tech.segmentation_logic if tech else plan.get("notes", "spot-level default")

    tissue_mask = None
    nuclei_mask = None
    cell_mask = None
    compartment_labels = None
    boundary_map = None
    warnings: list[str] = []

    if image is None:
        image = _synthetic_he_image()

    source = (segmentation_source or "run_tissue").lower()
    if source in ("uploaded", "imported") and imported_mask is not None:
        tissue_mask = imported_mask
    elif source == "run_tissue":
        try:
            tissue_mask = segment_tissue(image=image, method=tissue_method)
        except Exception as exc:
            warnings.append(f"tissue segmentation failed: {exc}")

    registration = register_spatial_to_image(adata, image=image)
    reg_validation = validate_registration(adata, tissue_mask)

    if source == "voronoi" or cell_method == "voronoi":
        coords = np.asarray(adata.obsm["spatial"])
        clip = None
        if tissue_mask is not None and tissue_mask.ndim >= 2:
            clip = np.array([
                tissue_mask[min(int(y), tissue_mask.shape[0] - 1), min(int(x), tissue_mask.shape[1] - 1)] > 0
                for x, y in coords
            ])
        cell_mask = generate_voronoi_cells(coords, clip_mask=clip)
    elif source in ("run_nuclei", "run_cells"):
        try:
            nuclei_mask = segment_nuclei(image, method=cell_method if cell_method != "voronoi" else "watershed")
            cell_mask = segment_cells(image, nuclei_mask=nuclei_mask, method=cell_method)
        except Exception as exc:
            warnings.append(f"cell segmentation failed: {exc}")
            cell_mask = generate_voronoi_cells(np.asarray(adata.obsm["spatial"]))

    try:
        compartment_labels = segment_compartments(image=image, adata=adata, method=compartment_method)
    except Exception as exc:
        warnings.append(f"compartment segmentation failed: {exc}")

    boundary_result = None
    if compartment_labels is not None:
        adata_tmp = attach_segmentation_to_adata(adata, compartment_labels=compartment_labels)
        boundary_result = detect_boundaries(compartment_labels, adata=adata_tmp)
        boundary_map = boundary_result.get("boundary_score")

    segmentation_qc = compute_segmentation_qc(
        adata=adata,
        tissue_mask=tissue_mask,
        nuclei_mask=nuclei_mask,
        cell_mask=cell_mask,
        boundary_map=boundary_map,
        registration=reg_validation,
        image=image,
    )
    warnings.extend(segmentation_qc.get("warnings", []))

    methods = {
        "tissue": tissue_method,
        "cells": cell_method,
        "compartments": compartment_method,
        "source": segmentation_source,
    }
    adata_out = attach_segmentation_to_adata(
        adata,
        tissue_mask=tissue_mask if tissue_mask is not None and tissue_mask.ndim == 1 else None,
        nuclei_mask=nuclei_mask,
        cell_mask=cell_mask,
        compartment_labels=compartment_labels,
        boundary_map=boundary_map,
        segmentation_qc=segmentation_qc,
        methods=methods,
    )

    export_paths: Dict[str, str] = {}
    if out_dir is not None:
        export_paths = export_segmentation_masks(
            out_dir,
            tissue_mask=tissue_mask if tissue_mask is not None and tissue_mask.ndim >= 2 else None,
            nuclei_mask=nuclei_mask,
            cell_mask=cell_mask if cell_mask is not None and getattr(cell_mask, "ndim", 0) >= 2 else None,
        )

    _, seg_findings = build_segmentation_findings(
        adata_out,
        boundary_result=boundary_result,
        segmentation_qc=segmentation_qc,
    )

    return RunRecord.success(
        module=WorkflowModule.SEGMENT_REGISTER.value,
        inputs={
            "technology_key": technology_key,
            "tissue_method": tissue_method,
            "cell_method": cell_method,
            "compartment_method": compartment_method,
            "segmentation_source": segmentation_source,
        },
        outputs={
            "segmentation_logic": logic,
            "technology_plan": plan,
            "has_segmentation": tissue_mask is not None or cell_mask is not None,
            "tissue_mask": tissue_mask,
            "nuclei_mask": nuclei_mask,
            "cell_mask": cell_mask,
            "compartment_labels": compartment_labels,
            "boundary_map": boundary_map,
            "segmentation_qc": segmentation_qc,
            "registration": registration,
            "registration_validation": reg_validation,
            "export_paths": export_paths,
            "segmentation_findings": seg_findings,
            "adata": adata_out,
            "status": "segment_complete",
        },
        warnings=warnings,
    )
