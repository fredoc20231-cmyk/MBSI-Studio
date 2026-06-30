"""API contract tests — each endpoint returns valid JSON structure."""

from __future__ import annotations

import json
from pathlib import Path

import anndata as ad
import numpy as np
import pytest

from mbsi.api import handlers
from mbsi.api.contracts import (
    DatasetInspectRequest,
    DatasetUploadRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ReportGenerateRequest,
    WorkflowRunRequest,
)
from mbsi.api.router import route


@pytest.fixture
def registry_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data" / "registry" / "projects").mkdir(parents=True)
    (tmp_path / "data" / "registry" / "datasets").mkdir(parents=True)
    (tmp_path / "data" / "outputs" / "reports").mkdir(parents=True)
    return tmp_path


def _assert_json_serializable(payload):
    text = json.dumps(payload, default=str)
    assert json.loads(text) is not None


def test_project_create_update(registry_root):
    created = handlers.create_project(ProjectCreateRequest(title="Test Project", organism="Human"))
    payload = created.model_dump()
    _assert_json_serializable(payload)
    assert payload["project_id"]
    assert payload["project"]["title"] == "Test Project"

    updated = handlers.update_project(
        ProjectUpdateRequest(project_id=payload["project_id"], biological_question="What niches exist?")
    )
    up = updated.model_dump()
    _assert_json_serializable(up)
    assert up["project"]["biological_question"] == "What niches exist?"


def test_dataset_upload_h5ad(registry_root, tmp_path):
    x = np.random.poisson(3, (20, 30)).astype(float)
    adata = ad.AnnData(X=x)
    adata.var_names = [f"g{i}" for i in range(30)]
    adata.obs_names = [f"s{i}" for i in range(20)]
    adata.obsm["spatial"] = np.column_stack([np.random.rand(20), np.random.rand(20)])
    h5ad_path = tmp_path / "test.h5ad"
    adata.write_h5ad(h5ad_path)

    uploaded = handlers.upload_dataset(
        DatasetUploadRequest(project_id="proj1", technology_hint="generic_h5ad"),
        source_path=str(h5ad_path),
    )
    data = uploaded.model_dump()
    _assert_json_serializable(data)
    assert data["dataset_id"]
    assert data["platform"]
    assert "readiness" in data
    assert "compatibility" in data
    assert isinstance(data["warnings"], list)


def test_dataset_inspect_and_readiness(registry_root):
    inspected = handlers.inspect_dataset(DatasetInspectRequest(dataset_id="missing-id"))
    data = inspected.model_dump()
    _assert_json_serializable(data)
    assert data["warnings"]

    ready = handlers.dataset_readiness("missing-id").model_dump()
    _assert_json_serializable(ready)
    assert ready["readiness"]["status"] == "not_found"


def test_workflow_run_status_no_data(registry_root):
    run = handlers.run_workflow(
        WorkflowRunRequest(module="discovery", dataset_id="default", allow_demo=False)
    ).model_dump()
    _assert_json_serializable(run)
    assert run["run_id"]
    assert run["module"] == "discovery"

    status = handlers.workflow_status(run["run_id"]).model_dump()
    _assert_json_serializable(status)
    assert status["run_id"] == run["run_id"]


def test_results_findings_evidence_report(registry_root):
    results = handlers.list_results("default").model_dump()
    _assert_json_serializable(results)
    assert "results" in results

    findings = handlers.list_findings(run_id="none").model_dump()
    _assert_json_serializable(findings)
    assert "findings" in findings

    evidence = handlers.list_evidence(run_id="none").model_dump()
    _assert_json_serializable(evidence)
    assert "evidence" in evidence

    report = handlers.generate_report(ReportGenerateRequest(project_id="", report_type="json")).model_dump()
    _assert_json_serializable(report)
    assert report["report_id"]
    assert report["report"]


def test_router_function_layer(registry_root):
    out = route("POST", "/api/project/create", {"title": "Router Project"})
    _assert_json_serializable(out)
    assert out["project_id"]

    out2 = route("GET", "/api/results/list", dataset_id="default")
    _assert_json_serializable(out2)

    out3 = route("POST", "/api/report/generate", {"report_type": "json"})
    _assert_json_serializable(out3)
