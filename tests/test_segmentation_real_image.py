"""Integration tests for real-image segmentation workflow."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.segmentation.export import export_boundaries, export_label_mask
from mbsi.segmentation.importers import load_segmentation_mask, rasterize_boundaries
from mbsi.segmentation.qc import compute_label_mask_qc
from mbsi.workflows.segment_register import run_cell_boundary_segmentation, run_segment_register_workflow


def _circle_image(size: int = 96) -> np.ndarray:
    image = np.zeros((size, size), dtype=np.uint8)
    ys, xs = np.ogrid[:size, :size]
    for cx, cy, r in [(24, 24, 10), (68, 30, 9), (45, 70, 11)]:
        image[(xs - cx) ** 2 + (ys - cy) ** 2 <= r ** 2] = 220
    return np.stack([image, image, image], axis=-1)


def _boundary_df_for_image(size: int = 96) -> pd.DataFrame:
    rows = []
    squares = [(14, 14, 34, 34, 1), (58, 20, 78, 40, 2), (34, 59, 56, 81, 3)]
    for x0, y0, x1, y1, label in squares:
        coords = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        for x, y in coords:
            rows.append({"cell_id": f"cell_{label}", "vertex_x": x, "vertex_y": y, "label_id": label})
    return pd.DataFrame(rows)


def test_imported_boundaries_from_vertices():
    df = _boundary_df_for_image()
    mask, _ = rasterize_boundaries(df, shape=(96, 96), pixel_size_microns=1.0)
    qc = compute_label_mask_qc(mask)
    assert qc["n_cells"] == 3
    assert qc["median_cell_area"] > 0


def test_workflow_imported_boundaries(tmp_path):
    adata = make_synthetic_visium_adata(n_spots=30)
    image = _circle_image()
    df = _boundary_df_for_image()
    mask, _ = rasterize_boundaries(df, shape=image.shape[:2], pixel_size_microns=1.0)
    run = run_segment_register_workflow(
        adata,
        technology_key="xenium",
        image=image,
        cell_method="imported_boundaries",
        imported_mask=mask,
        out_dir=tmp_path,
        allow_synthetic_image=False,
    )
    assert run.status == "success"
    metrics = run.outputs["segmentation_qc"]["metrics"]
    assert metrics.get("n_cells", metrics.get("cell_count", 0)) >= 3
    assert "median_cell_area" in metrics
    assert run.outputs["export_paths"].get("cells") or run.outputs["export_paths"].get("cells_npy")


def test_download_mask_export_roundtrip(tmp_path):
    df = _boundary_df_for_image()
    mask, _ = rasterize_boundaries(df, shape=(96, 96), pixel_size_microns=1.0)
    mask_path = export_label_mask(tmp_path / "cells.npy", mask)
    loaded = load_segmentation_mask(mask_path)
    np.testing.assert_array_equal(loaded, mask)
    boundary_path = export_boundaries(tmp_path / "boundaries.parquet", label_mask=mask)
    assert Path(boundary_path).exists()


def test_voronoi_from_coordinates():
    adata = make_synthetic_visium_adata(n_spots=25)
    image = _circle_image()
    result = run_cell_boundary_segmentation(
        method="voronoi",
        image=image,
        adata=adata,
    )
    assert result["cell_mask"] is not None


def test_stardist_workflow_when_installed(tmp_path):
    pytest.importorskip("stardist")
    pytest.importorskip("tensorflow")
    from mbsi.segmentation.adapters import stardist_available

    if not stardist_available():
        pytest.skip("StarDist unavailable")

    adata = make_synthetic_visium_adata(n_spots=20)
    image = _circle_image()
    run = run_segment_register_workflow(
        adata,
        image=image,
        cell_method="stardist_expansion",
        expansion_pixels=4,
        out_dir=tmp_path,
        allow_synthetic_image=False,
    )
    assert run.status == "success"
    cell_mask = run.outputs["cell_mask"]
    assert cell_mask is not None
    assert cell_mask.max() > 0
    metrics = run.outputs["segmentation_qc"]["metrics"]
    assert metrics.get("n_cells", metrics.get("cell_count", 0)) > 0


def test_transcript_mapping_in_workflow(tmp_path):
    adata = make_synthetic_visium_adata(n_spots=10)
    df = _boundary_df_for_image()
    mask, _ = rasterize_boundaries(df, shape=(96, 96), pixel_size_microns=1.0)
    transcripts = pd.DataFrame(
        {
            "x": [20, 21, 65, 45, 200],
            "y": [20, 21, 30, 70, 10],
            "gene": ["G1", "G1", "G2", "G3", "G4"],
        }
    )
    run = run_segment_register_workflow(
        adata,
        image=_circle_image(),
        cell_method="imported_boundaries",
        imported_mask=mask,
        transcript_df=transcripts,
        map_transcripts=True,
        out_dir=tmp_path,
        allow_synthetic_image=False,
    )
    assert run.status == "success"
    assert run.outputs.get("transcript_adata") is not None
    metrics = run.outputs["segmentation_qc"]["metrics"]
    assert metrics.get("percent_transcripts_assigned") is not None
