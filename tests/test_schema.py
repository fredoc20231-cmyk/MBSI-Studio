"""Tests for mbsi.schema spine and technology catalog."""

from mbsi.schema import (
    TECHNOLOGY_CATALOG,
    UI_TECHNOLOGY_OPTIONS,
    WorkflowModule,
    WORKFLOW_SUBSTEPS,
    get_technology,
    resolve_module_key,
)
from mbsi.schema.project import ProjectMetadata
from mbsi.schema.sample import SampleRecord
from mbsi.io.compatibility import get_compatibility_matrix


def test_technology_catalog_keys():
    expected = {
        "visium",
        "visium_hd",
        "xenium",
        "merfish",
        "cosmx",
        "stereo_seq",
        "codex",
        "spatial_atac",
        "generic_h5ad",
    }
    assert set(TECHNOLOGY_CATALOG.keys()) == expected
    assert len(UI_TECHNOLOGY_OPTIONS) == 9


def test_stereo_seq_spec():
    spec = get_technology("stereo_seq")
    assert spec is not None
    required = " ".join(spec.required_files).lower()
    assert "gef" in required or "cgef" in required
    assert "saw" in required or "stereomap" in required
    assert "benchmark" in spec.compatible_analyses


def test_workflow_modules():
    assert len(WorkflowModule) == 10
    assert WorkflowModule.STUDY_SETUP.value == "study_setup"
    assert "communication" in WORKFLOW_SUBSTEPS[WorkflowModule.DISCOVERY.value]
    assert resolve_module_key("project_setup") == "study_setup"
    assert resolve_module_key("notebook") == "report_export"


def test_project_metadata_from_session():
    meta = ProjectMetadata.from_session({"project_title": "Test", "organism": "Mouse"})
    assert meta.title == "Test"
    assert meta.organism == "Mouse"


def test_sample_record_roundtrip():
    s = SampleRecord(sample_id="S1", condition="Case", comparison_group="A vs B")
    restored = SampleRecord.from_dict(s.to_dict())
    assert restored.sample_id == "S1"
    assert restored.comparison_group == "A vs B"


def test_compatibility_uses_workflow_keys():
    matrix = get_compatibility_matrix(None)
    assert "study_setup" in matrix
    assert "qc_preprocess" in matrix
    assert matrix["study_setup"]["status"] == "available"
    assert matrix["qc_preprocess"]["status"] == "unavailable"
