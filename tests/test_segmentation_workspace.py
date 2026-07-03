"""Tests for segmentation workspace and workflow wiring."""

import numpy as np

from mbsi.analysis.demo import make_synthetic_visium_adata
from mbsi.workflows.segment_register import run_segment_register_workflow


def test_workflow_imports_and_runs():
    adata = make_synthetic_visium_adata(n_spots=40)
    rng = np.random.default_rng(3)
    image = rng.integers(0, 255, (64, 64, 3), dtype=np.uint8)
    run = run_segment_register_workflow(
        adata,
        technology_key="visium",
        image=image,
        tissue_method="otsu",
        cell_method="voronoi",
        compartment_method="hybrid",
        allow_synthetic_image=False,
    )
    assert run.status == "success"
    assert run.outputs["status"] == "segment_complete"
    assert run.outputs["segmentation_qc"] is not None
    assert "mbsi_segmentation" in run.outputs["adata"].uns


def test_workspace_module_import():
    from app.workspaces import segment_register
    assert hasattr(segment_register, "render")


def test_segmentation_findings_gated():
    from mbsi.discovery.segmentation_findings import build_segmentation_findings
    adata = make_synthetic_visium_adata(n_spots=50)
    adata.obs["compartment"] = ["tumor"] * 40 + ["immune"] * 5 + ["stroma"] * 5
    _, findings = build_segmentation_findings(adata, segmentation_qc={"qc_pass": False})
    assert findings == []
