"""Tests for segmentation QC metrics."""

import numpy as np

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.segmentation import compute_segmentation_qc
from mbsi.segmentation.tissue import segment_tissue


def test_qc_fields_present():
    adata = make_synthetic_visium_adata(n_spots=30)
    rng = np.random.default_rng(2)
    image = rng.integers(0, 255, (48, 48, 3), dtype=np.uint8)
    tissue = segment_tissue(image=image, method="otsu")
    qc = compute_segmentation_qc(adata=adata, tissue_mask=tissue, image=image)
    assert "metrics" in qc
    assert "warnings" in qc
    assert "qc_pass" in qc
    assert "percent_tissue_covered" in qc["metrics"]
    assert "segmentation_confidence" in qc["metrics"]


def test_qc_warns_no_segmentation():
    qc = compute_segmentation_qc()
    assert qc["qc_pass"] is False or len(qc["warnings"]) > 0


def test_qc_cell_counts():
    cell_mask = np.arange(20, dtype=np.int32)
    qc = compute_segmentation_qc(cell_mask=cell_mask)
    assert qc["metrics"]["cell_count"] == 20
