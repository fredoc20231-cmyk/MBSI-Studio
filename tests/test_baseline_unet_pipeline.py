"""Tests for optional baseline U-Net and Mesmer pipelines."""

from __future__ import annotations

import numpy as np
import pytest

from mbsi.segmentation.baseline_unet import (
    UNTRAINED_MESSAGE,
    baseline_unet_weights_available,
    run_baseline_unet_segmentation,
)
from mbsi.segmentation.deepcell_mesmer_pipeline import mesmer_available, run_mesmer_segmentation


def _tiny_image() -> np.ndarray:
    return np.stack([np.full((32, 32), 180, dtype=np.uint8)] * 3, axis=-1)


@pytest.mark.unit
def test_baseline_unet_untrained_unavailable(tmp_path, monkeypatch):
    monkeypatch.setenv("MBSI_BASELINE_UNET_WEIGHTS", str(tmp_path / "missing.pt"))
    assert baseline_unet_weights_available() is False
    with pytest.raises(RuntimeError, match="Untrained baseline unavailable"):
        run_baseline_unet_segmentation(_tiny_image())


@pytest.mark.unit
def test_baseline_unet_rejects_empty_weights(tmp_path, monkeypatch):
    weights = tmp_path / "empty.pt"
    weights.write_bytes(b"")
    monkeypatch.setenv("MBSI_BASELINE_UNET_WEIGHTS", str(weights))
    assert baseline_unet_weights_available() is False


@pytest.mark.unit
def test_untrained_message_is_actionable():
    assert "data/models/baseline_unet.pt" in UNTRAINED_MESSAGE


@pytest.mark.unit
def test_mesmer_import_guard():
    if not mesmer_available():
        with pytest.raises(ImportError, match="DeepCell"):
            run_mesmer_segmentation(_tiny_image())
