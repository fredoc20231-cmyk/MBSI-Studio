"""Tests for Xenium boundary import."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mbsi.io.xenium import apply_xenium_boundaries, read_xenium_bundle
from mbsi.segmentation.importers import load_xenium_boundaries
from tests.test_xenium_ingestion import write_mini_xenium_bundle


def _write_boundaries_parquet(root: Path, n_cells: int = 4) -> Path:
    rows = []
    for i in range(n_cells):
        cx, cy = float(i * 20 + 10), float(i * 15 + 10)
        square = [
            (cx - 5, cy - 5),
            (cx + 5, cy - 5),
            (cx + 5, cy + 5),
            (cx - 5, cy + 5),
            (cx - 5, cy - 5),
        ]
        for x, y in square:
            rows.append({"cell_id": f"cell_{i:04d}", "vertex_x": x, "vertex_y": y, "label_id": i + 1})
    path = root / "cell_boundaries.parquet"
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def test_load_xenium_boundaries(tmp_path):
    boundaries_path = _write_boundaries_parquet(tmp_path)
    result = load_xenium_boundaries(boundaries_path, pixel_size_microns=1.0)
    assert result["n_cells"] == 4
    assert result["label_mask"].shape[0] > 0
    assert result["label_mask"].max() == 4


def test_xenium_bundle_auto_imports_boundaries(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=8, n_genes=20)
    _write_boundaries_parquet(tmp_path)
    adata = read_xenium_bundle(tmp_path)
    assert "boundaries" in adata.uns["xenium"]["optional_artifacts"]
    assert adata.uns["mbsi_segmentation"]["segmentation_status"] == "Imported Xenium boundaries"
    assert isinstance(adata.uns["mbsi_cell_label_mask"], np.ndarray)
    assert adata.uns["mbsi_segmentation"]["n_cells"] >= 1


def test_apply_xenium_boundaries_standalone(tmp_path):
    write_mini_xenium_bundle(tmp_path, n_cells=6, n_genes=15)
    boundaries_path = _write_boundaries_parquet(tmp_path, n_cells=3)
    adata = read_xenium_bundle(tmp_path)
    adata.uns["xenium"]["optional_artifacts"] = {"boundaries": str(boundaries_path)}
    adata.uns.pop("mbsi_cell_label_mask", None)
    adata.uns.pop("mbsi_segmentation", None)
    updated = apply_xenium_boundaries(adata, boundaries_path)
    assert updated.uns["mbsi_segmentation"]["segmentation_status"] == "Imported Xenium boundaries"
