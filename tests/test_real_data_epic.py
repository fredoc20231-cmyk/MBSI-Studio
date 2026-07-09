"""Tests for real-data platform reorganization epic gaps."""

import pytest

from mbsi.discovery.engine import run_discovery_engine
from mbsi.io.compatibility import get_compatibility_matrix, recommended_next_step_for_module
from mbsi.io.ingest import LOADER_CONTRACT_KEYS, normalize_loader_result
from mbsi.schema import AnalysisResult, Confidence, StudyDesign
from mbsi.schema.sample import SampleRecord
from mbsi.tme import make_tme_demo_adata


def test_study_design_from_session():
    design = StudyDesign.from_session(
        {
            "study_type": "Case-control",
            "primary_comparison": "Case vs Control",
            "secondary_comparisons": "Treated vs Untreated",
            "timepoints": "Baseline, Week 4",
            "treatment_arms": "Arm A, Arm B",
        },
        project_id="proj-1",
    )
    assert design.study_type == "Case-control"
    assert design.primary_comparison == "Case vs Control"
    assert design.timepoints == ["Baseline", "Week 4"]
    assert design.project_id == "proj-1"


def test_analysis_result_traceability():
    result = AnalysisResult.from_run(
        module="discovery",
        result_type="findings",
        run_id="run-123",
        payload={"n": 3},
        context={
            "project_id": "p1",
            "sample_id": "S1",
            "condition": "Case",
            "replicate_id": "R1",
            "technology": "visium",
            "dataset_id": "ds1",
        },
    )
    d = result.to_dict()
    assert d["run_id"] == "run-123"
    assert d["sample_id"] == "S1"
    assert d["technology"] == "visium"


def test_confidence_from_finding():
    from mbsi.discovery_model.entities import Finding

    finding = Finding.create(
        title="Test",
        summary="s",
        finding_type="benchmark",
        module="benchmark",
        confidence_score=80.0,
        confidence_level="High",
        sample_id="S1",
    )
    conf = Confidence.from_finding(finding, run_id="run-abc", project_id="p1", technology="visium")
    assert conf.level == "High"
    assert conf.run_id == "run-abc"
    assert conf.sample_id == "S1"


def test_sample_technology_column():
    s = SampleRecord(sample_id="S1", technology="10x Visium", platform="10x Visium")
    assert s.to_dict()["technology"] == "10x Visium"


def test_discovery_no_demo_default():
    out = run_discovery_engine(adata=None, allow_demo=False)
    assert out["status"] == "unavailable"
    assert out["findings"] == []
    assert "upload real data" in out["warnings"][0].lower()


def test_discovery_allow_demo():
    out = run_discovery_engine(allow_demo=True, seed=42)
    assert out["status"] in ("complete", "complete_with_warnings")
    assert out.get("is_demo") is True
    assert len(out["findings"]) >= 1


def test_discovery_real_data_includes_run_id():
    adata = make_tme_demo_adata(n_spots=80, seed=1)
    out = run_discovery_engine(adata=adata, seed=1, allow_demo=False)
    assert out.get("run_id")
    assert all(f.get("run_id") for f in out["findings"])


def test_compatibility_recommended_next_step():
    matrix = get_compatibility_matrix(None)
    assert matrix["discovery"]["status"] in ("unavailable", "warn")
    step = recommended_next_step_for_module("discovery", matrix["discovery"]["status"], ["spatial omics upload"], has_adata=False)
    assert "upload" in step.lower()


def test_loader_contract_keys():
    result = normalize_loader_result({"platform": "visium", "readiness": {"score": 0}})
    for key in LOADER_CONTRACT_KEYS:
        assert key in result
