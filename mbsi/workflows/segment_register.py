"""Segmentation and registration workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd

from mbsi.discovery.segmentation_findings import build_segmentation_findings
from mbsi.schema.run import RunRecord
from mbsi.schema.technology import get_technology
from mbsi.schema.workflow import WorkflowModule
from mbsi.segmentation import (
    attach_segmentation_to_adata,
    build_cell_by_gene_anndata,
    compute_segmentation_qc,
    detect_boundaries,
    expand_nuclei_to_cells,
    export_boundaries,
    export_label_mask,
    export_segmentation_masks,
    generate_voronoi_cells,
    load_xenium_boundaries,
    register_spatial_to_image,
    run_cellpose_segmentation,
    run_mesmer_segmentation,
    run_baseline_unet_segmentation,
    run_stardist_nuclei_segmentation,
    segment_compartments,
    segment_tissue,
    validate_registration,
    voronoi_label_mask_from_coords,
)
from mbsi.segmentation.adapters import (
    baseline_unet_available,
    cellpose_available,
    get_technology_segmentation_plan,
    mesmer_available,
    segment_cells_watershed,
    stardist_available,
)
from mbsi.segmentation.baseline_unet import UNTRAINED_MESSAGE
from mbsi.segmentation.importers import load_boundary_csv, load_boundary_geojson, load_segmentation_mask


def _synthetic_he_image(n: int = 128) -> np.ndarray:
    rng = np.random.default_rng(42)
    img = rng.integers(180, 240, (n, n, 3), dtype=np.uint8)
    img[20:100, 20:100] = rng.integers(80, 160, (80, 80, 3), dtype=np.uint8)
    return img


def run_cell_boundary_segmentation(
    *,
    method: str,
    image: Optional[np.ndarray] = None,
    adata: Any = None,
    imported_mask: Optional[np.ndarray] = None,
    boundary_path: Optional[Union[str, Path]] = None,
    expansion_pixels: int = 5,
    channel: Optional[Union[int, str]] = None,
    tissue_mask: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Run Milestone 1 high-resolution cell boundary segmentation."""
    method = (method or "voronoi").lower()
    nuclei_mask = None
    cell_mask = None
    boundaries_df = None
    warnings: list[str] = []

    if method in ("imported", "imported_boundaries", "xenium_boundaries"):
        if imported_mask is not None:
            cell_mask = np.asarray(imported_mask, dtype=np.int32)
        elif boundary_path is not None:
            boundary_path = Path(boundary_path)
            suffix = boundary_path.suffix.lower()
            if suffix == ".parquet" and "cell_boundaries" in boundary_path.name:
                loaded = load_xenium_boundaries(
                    boundary_path,
                    shape=image.shape[:2] if image is not None else None,
                )
                cell_mask = loaded["label_mask"]
                boundaries_df = loaded["boundaries_df"]
            elif suffix == ".geojson":
                df = load_boundary_geojson(boundary_path)
                from mbsi.segmentation.importers import rasterize_boundaries

                cell_mask, _ = rasterize_boundaries(
                    df,
                    shape=image.shape[:2] if image is not None else None,
                )
                boundaries_df = df
            else:
                df = load_boundary_csv(boundary_path)
                from mbsi.segmentation.importers import rasterize_boundaries

                cell_mask, _ = rasterize_boundaries(
                    df,
                    shape=image.shape[:2] if image is not None else None,
                )
                boundaries_df = df
        else:
            raise ValueError("Imported boundaries require an uploaded mask or boundary file")

    elif method in ("stardist", "stardist_expansion", "stardist_nuclei"):
        if image is None:
            raise ValueError("StarDist requires a real uploaded morphology image")
        if not stardist_available():
            raise ImportError("StarDist is not installed")
        nuclei_mask = run_stardist_nuclei_segmentation(image, channel=channel)
        cell_mask = expand_nuclei_to_cells(nuclei_mask, expansion_pixels=expansion_pixels)

    elif method in ("cellpose", "omnipose"):
        if image is None:
            raise ValueError("Cellpose/Omnipose requires a real uploaded morphology image")
        if not cellpose_available():
            raise ImportError("Cellpose is not installed. Install with: pip install cellpose")
        model_type = "nuclei" if method == "cellpose" else "cyto2"
        cell_mask = run_cellpose_segmentation(image, model_type=model_type)

    elif method in ("mesmer", "deepcell", "deepcell_mesmer"):
        if image is None:
            raise ValueError("Mesmer/DeepCell requires a real uploaded morphology image")
        if not mesmer_available():
            raise ImportError("DeepCell Mesmer is not installed. Install with: pip install deepcell")
        cell_mask = run_mesmer_segmentation(image, compartment="whole-cell")

    elif method in ("baseline_unet", "unet_baseline", "baseline"):
        if image is None:
            raise ValueError("Baseline U-Net requires a real uploaded morphology image")
        if not baseline_unet_available():
            raise RuntimeError(UNTRAINED_MESSAGE)
        cell_mask = run_baseline_unet_segmentation(image)

    elif method == "watershed":
        if image is None:
            raise ValueError("Watershed fallback requires a real uploaded morphology image")
        cell_mask = segment_cells_watershed(image).astype(np.int32)

    elif method == "voronoi":
        if adata is None or "spatial" not in adata.obsm:
            raise ValueError("Voronoi segmentation requires spatial coordinates in adata.obsm['spatial']")
        coords = np.asarray(adata.obsm["spatial"])
        if image is not None:
            clip = tissue_mask.astype(bool) if tissue_mask is not None else None
            cell_mask = voronoi_label_mask_from_coords(coords, image.shape[:2], clip_mask=clip)
        else:
            cell_mask = generate_voronoi_cells(coords, clip_mask=None)
    else:
        raise ValueError(f"Unsupported segmentation method: {method}")

    return {
        "nuclei_mask": nuclei_mask,
        "cell_mask": cell_mask,
        "boundaries_df": boundaries_df,
        "warnings": warnings,
    }


def run_segment_register_workflow(
    adata: Any,
    technology_key: str = "",
    image: Optional[np.ndarray] = None,
    tissue_method: str = "otsu",
    cell_method: str = "voronoi",
    compartment_method: str = "hybrid",
    segmentation_source: str = "run_tissue",
    imported_mask: Optional[np.ndarray] = None,
    boundary_path: Optional[Union[str, Path]] = None,
    transcript_df: Optional[pd.DataFrame] = None,
    expansion_pixels: int = 5,
    channel: Optional[Union[int, str]] = None,
    map_transcripts: bool = False,
    out_dir: Optional[Path] = None,
    allow_synthetic_image: bool = False,
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
    boundaries_df = None
    transcript_adata = None
    warnings: list[str] = []

    source = (segmentation_source or "run_tissue").lower()
    method = (cell_method or "voronoi").lower()

    xenium_mask = adata.uns.get("mbsi_cell_label_mask") if isinstance(adata.uns.get("mbsi_cell_label_mask"), np.ndarray) else None
    if xenium_mask is not None and method in ("imported", "imported_boundaries", "xenium_boundaries", "imported_xenium_boundaries"):
        cell_mask = xenium_mask
        boundaries_df = adata.uns.get("mbsi_cell_boundaries")

    needs_image = method in (
        "stardist",
        "stardist_expansion",
        "stardist_nuclei",
        "cellpose",
        "omnipose",
        "mesmer",
        "deepcell",
        "deepcell_mesmer",
        "baseline_unet",
        "unet_baseline",
        "baseline",
        "watershed",
    ) or (
        source == "run_tissue" and tissue_method not in ("voronoi",)
    )

    if image is None and needs_image and imported_mask is None and cell_mask is None:
        if allow_synthetic_image:
            image = _synthetic_he_image()
            warnings.append("Using synthetic H&E placeholder (developer mode only).")
        else:
            return RunRecord.failed(
                WorkflowModule.SEGMENT_REGISTER.value,
                "No histology/morphology image found. Upload image in Study & Data or Segmentation page.",
            )

    if source in ("uploaded", "imported") and imported_mask is not None:
        tissue_mask = imported_mask
    elif source == "run_tissue" and image is not None:
        try:
            tissue_mask = segment_tissue(image=image, method=tissue_method)
        except Exception as exc:
            warnings.append(f"tissue segmentation failed: {exc}")

    registration = register_spatial_to_image(adata, image=image) if image is not None else {"status": "skipped", "reason": "no image"}
    reg_validation = validate_registration(adata, tissue_mask)

    if cell_mask is None:
        try:
            seg_result = run_cell_boundary_segmentation(
                method=method,
                image=image,
                adata=adata,
                imported_mask=imported_mask if method.startswith("imported") else None,
                boundary_path=boundary_path,
                expansion_pixels=expansion_pixels,
                channel=channel,
                tissue_mask=tissue_mask,
            )
            nuclei_mask = seg_result.get("nuclei_mask")
            cell_mask = seg_result.get("cell_mask")
            boundaries_df = seg_result.get("boundaries_df")
            warnings.extend(seg_result.get("warnings", []))
        except ImportError as exc:
            return RunRecord.failed(WorkflowModule.SEGMENT_REGISTER.value, str(exc))
        except RuntimeError as exc:
            return RunRecord.failed(WorkflowModule.SEGMENT_REGISTER.value, str(exc))
        except Exception as exc:
            warnings.append(f"cell segmentation failed: {exc}")
            if method != "voronoi":
                return RunRecord.failed(WorkflowModule.SEGMENT_REGISTER.value, str(exc))

    if map_transcripts:
        if transcript_df is None:
            warnings.append("Transcript mapping requested but no transcripts file uploaded")
        elif cell_mask is None or getattr(cell_mask, "ndim", 0) < 2:
            warnings.append("Transcript mapping requires a 2D label mask")
        else:
            try:
                transcript_adata = build_cell_by_gene_anndata(transcript_df, cell_mask)
            except Exception as exc:
                warnings.append(f"transcript mapping failed: {exc}")

    try:
        compartment_labels = segment_compartments(image=image, adata=adata, method=compartment_method)
    except Exception as exc:
        warnings.append(f"compartment segmentation failed: {exc}")

    boundary_result = None
    if compartment_labels is not None:
        adata_tmp = attach_segmentation_to_adata(adata, compartment_labels=compartment_labels)
        boundary_result = detect_boundaries(compartment_labels, adata=adata_tmp)
        boundary_map = boundary_result.get("boundary_score")
    elif cell_mask is not None and getattr(cell_mask, "ndim", 0) >= 2:
        boundary_result = detect_boundaries(cell_mask, adata=adata)
        boundary_map = boundary_result.get("boundary_score")

    label_for_qc = cell_mask if getattr(cell_mask, "ndim", 0) >= 2 else None
    segmentation_qc = compute_segmentation_qc(
        adata=adata,
        tissue_mask=tissue_mask,
        nuclei_mask=nuclei_mask,
        cell_mask=cell_mask,
        label_mask=label_for_qc,
        boundary_map=boundary_map,
        registration=reg_validation,
        image=image,
        transcript_df=transcript_df if map_transcripts else None,
    )
    warnings.extend(segmentation_qc.get("warnings", []))

    methods = {
        "tissue": tissue_method,
        "cells": cell_method,
        "compartments": compartment_method,
        "source": segmentation_source,
        "expansion_pixels": expansion_pixels,
        "channel": channel,
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
    if transcript_adata is not None:
        adata_out.uns["mbsi_transcript_cell_adata"] = transcript_adata

    export_paths: Dict[str, str] = {}
    if out_dir is not None:
        export_paths = export_segmentation_masks(
            out_dir,
            tissue_mask=tissue_mask if tissue_mask is not None and tissue_mask.ndim >= 2 else None,
            nuclei_mask=nuclei_mask,
            cell_mask=cell_mask if cell_mask is not None and getattr(cell_mask, "ndim", 0) >= 2 else None,
        )
        if cell_mask is not None and getattr(cell_mask, "ndim", 0) >= 2:
            mask_path = export_label_mask(out_dir / "segmentation_cells.npy", cell_mask)
            export_paths["cells_npy"] = mask_path
            boundary_export = export_boundaries(
                out_dir / "segmentation_boundaries.parquet",
                label_mask=cell_mask,
                boundaries_df=boundaries_df if isinstance(boundaries_df, pd.DataFrame) else None,
            )
            export_paths["boundaries"] = boundary_export

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
            "expansion_pixels": expansion_pixels,
            "channel": channel,
            "map_transcripts": map_transcripts,
        },
        outputs={
            "segmentation_logic": logic,
            "technology_plan": plan,
            "has_segmentation": tissue_mask is not None or cell_mask is not None,
            "tissue_mask": tissue_mask,
            "nuclei_mask": nuclei_mask,
            "cell_mask": cell_mask,
            "boundaries_df": boundaries_df,
            "transcript_adata": transcript_adata,
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
