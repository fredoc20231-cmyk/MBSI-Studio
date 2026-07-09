"""Tests for transcript-to-cell mapping."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mbsi.segmentation.qc import compute_label_mask_qc
from mbsi.segmentation.transcript_mapping import build_cell_by_gene_anndata, map_transcripts_to_labels


def _label_mask_with_cells() -> np.ndarray:
    mask = np.zeros((40, 40), dtype=np.int32)
    mask[5:15, 5:15] = 1
    mask[20:30, 20:30] = 2
    return mask


def test_map_transcripts_to_labels():
    mask = _label_mask_with_cells()
    transcripts = pd.DataFrame(
        {
            "x": [10, 25, 5, 100],
            "y": [10, 25, 5, 10],
            "gene": ["A", "A", "B", "C"],
        }
    )
    mapped = map_transcripts_to_labels(transcripts, mask)
    assert "cell_label" in mapped.columns
    assert int(mapped.loc[0, "cell_label"]) == 1
    assert int(mapped.loc[1, "cell_label"]) == 2
    assert int(mapped.loc[3, "cell_label"]) == 0


def test_build_cell_by_gene_anndata():
    mask = _label_mask_with_cells()
    transcripts = pd.DataFrame(
        {
            "x": [10, 11, 25, 26, 25],
            "y": [10, 11, 25, 26, 27],
            "gene": ["A", "A", "B", "B", "B"],
        }
    )
    adata = build_cell_by_gene_anndata(transcripts, mask, pixel_to_micron_ratio=0.5)
    assert adata.n_obs == 2
    assert adata.n_vars >= 2
    assert "spatial" in adata.obsm
    assert adata.obsm["spatial"].shape == (2, 2)


def test_qc_percent_transcripts_assigned():
    mask = _label_mask_with_cells()
    transcripts = pd.DataFrame({"x": [10, 25, 100], "y": [10, 25, 10], "gene": ["A", "B", "C"]})
    qc = compute_label_mask_qc(mask, transcript_df=transcripts)
    assert qc["n_cells"] == 2
    assert qc["median_cell_area"] > 0
    assert qc["percent_transcripts_assigned"] == pytest.approx(66.67, rel=0.05)
