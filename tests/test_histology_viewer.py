"""Tests for real histology extraction and overlay helpers."""

import numpy as np

from mbsi.analysis.demo import make_synthetic_visium_adata


def test_extract_histology_from_visium_uns():
    from app.components.histology_viewer import extract_histology_from_adata

    adata = make_synthetic_visium_adata(n_spots=20, n_genes=30, seed=1)
    hires = np.random.randint(0, 255, (40, 50, 3), dtype=np.uint8)
    adata.uns["spatial"] = {
        "sample": {
            "images": {"hires": hires, "lowres": hires[::2, ::2]},
            "scalefactors": {"tissue_hires_scalef": 0.5, "tissue_lowres_scalef": 0.1},
        },
        "library_id": "sample",
    }
    img, source, lib = extract_histology_from_adata(adata)
    assert img is not None
    assert img.shape == hires.shape
    assert source == "Visium hires image"
    assert lib == "sample"


def test_get_active_histology_prefers_uploaded():
    from app.components.histology_viewer import get_active_histology_image

    uploaded = np.zeros((10, 10, 3), dtype=np.uint8)
    adata = make_synthetic_visium_adata(n_spots=10, seed=2)
    adata.uns["spatial"] = {
        "sample": {"images": {"hires": np.ones((8, 8, 3), dtype=np.uint8)}},
        "library_id": "sample",
    }

    class _State(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    state = _State(
        uploaded_image=uploaded,
        adata=adata,
        using_synthetic_demo=False,
        mbsi_platform="visium",
        selected_technology="visium",
    )

    import app.components.histology_viewer as hv

    original = hv.st.session_state
    hv.st.session_state = state
    try:
        img, source = get_active_histology_image(adata)
    finally:
        hv.st.session_state = original

    assert np.array_equal(img, uploaded)
    assert source == "Uploaded image"


def test_render_histology_overlay_returns_figure():
    from app.components.histology_viewer import render_histology_overlay

    adata = make_synthetic_visium_adata(n_spots=15, seed=3)
    img = np.random.randint(0, 255, (60, 80, 3), dtype=np.uint8)
    fig = render_histology_overlay(
        adata=adata,
        image=img,
        color="total_counts",
        return_figure=True,
    )
    assert fig is not None
    assert len(fig.data) >= 2


def test_segment_workflow_fails_without_image_by_default():
    from mbsi.workflows.segment_register import run_segment_register_workflow

    adata = make_synthetic_visium_adata(n_spots=20, seed=4)
    run = run_segment_register_workflow(
        adata,
        technology_key="visium",
        image=None,
        segmentation_source="run_tissue",
        allow_synthetic_image=False,
    )
    assert run.status != "success"
