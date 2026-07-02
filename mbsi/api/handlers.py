"""Business logic for Builder.io-facing API — delegates to mbsi/io, workflows, discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from mbsi.api.contracts import (
    DatasetInspectRequest,
    DatasetInspectResponse,
    DatasetReadinessResponse,
    DatasetUploadRequest,
    DatasetUploadResponse,
    EvidenceListResponse,
    FindingsListResponse,
    ProjectCreateRequest,
    ProjectCreateResponse,
    ProjectUpdateRequest,
    ProjectUpdateResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ResultsListResponse,
    TechnologyListResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowStatusResponse,
)
from mbsi.discovery.engine import run_discovery_engine
from mbsi.io.ingest_universal import ingest_dataset
from mbsi.registry.registry import ProjectRegistry
from mbsi.schema.project import ProjectMetadata
from mbsi.schema.report import ReportMetadata
from mbsi.schema.serialize import to_json_serializable
from mbsi.schema.technology import (
    MILESTONE_1_PLATFORMS,
    is_milestone_platform,
    list_technologies_api,
    normalize_technology_hint,
)
from mbsi.schema.workflow_run import WorkflowRun

_PROJECTS_DIR = Path("data/registry/projects")
_DATASETS_DIR = Path("data/registry/datasets")
_RUNS: Dict[str, WorkflowRun] = {}


def _ensure_dirs() -> None:
    _PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    _DATASETS_DIR.mkdir(parents=True, exist_ok=True)


def _project_path(project_id: str) -> Path:
    return _PROJECTS_DIR / f"{project_id}.json"


def _dataset_path(dataset_id: str) -> Path:
    return _DATASETS_DIR / f"{dataset_id}.json"


def create_project(req: ProjectCreateRequest) -> ProjectCreateResponse:
    _ensure_dirs()
    project = ProjectMetadata(
        title=req.title,
        biological_question=req.biological_question,
        disease_context=req.disease_context,
        study_objective=req.study_objective,
        organism=req.organism,
        therapeutic_context=req.therapeutic_context,
    )
    project.traceability.project_id = str(uuid4())
    payload = project.to_dict()
    _project_path(project.project_id).write_text(json.dumps(payload, indent=2))
    return ProjectCreateResponse(project_id=project.project_id, project=payload)


def update_project(req: ProjectUpdateRequest) -> ProjectUpdateResponse:
    _ensure_dirs()
    path = _project_path(req.project_id)
    if not path.exists():
        project = ProjectMetadata.from_dict({"project_id": req.project_id})
    else:
        project = ProjectMetadata.from_dict(json.loads(path.read_text()))
    for field in (
        "title",
        "biological_question",
        "disease_context",
        "study_objective",
        "organism",
        "therapeutic_context",
    ):
        value = getattr(req, field)
        if value is not None:
            setattr(project, field, value)
    payload = project.to_dict()
    path.write_text(json.dumps(payload, indent=2))
    return ProjectUpdateResponse(project_id=req.project_id, project=payload)


def upload_dataset(
    req: DatasetUploadRequest,
    *,
    source_path: str,
) -> DatasetUploadResponse:
    _ensure_dirs()
    hint, hint_warning = normalize_technology_hint(req.technology_hint)
    effective_hint = hint if hint is not None else req.technology_hint
    result = ingest_dataset(source_path, technology_hint=effective_hint)
    record = result.to_dict()
    record["project_id"] = req.project_id
    record["sample_id"] = req.sample_id
    _dataset_path(result.dataset_id).write_text(json.dumps(record, indent=2, default=str))
    summary = {
        "n_obs": record.get("metadata", {}).get("n_obs", 0),
        "n_vars": record.get("metadata", {}).get("n_vars", 0),
    }
    warnings = list(result.warnings)
    if hint_warning:
        warnings.insert(0, hint_warning)
    platform = result.platform
    if not is_milestone_platform(platform) and platform not in ("csv_matrix", "unknown"):
        warnings.append(
            f"Detected platform '{platform}' is not in Milestone 1 scope — pipeline modules are Coming later"
        )
    return DatasetUploadResponse(
        dataset_id=result.dataset_id,
        adata_path=result.adata_path,
        platform=platform,
        technology_profile=result.technology_profile,
        readiness=result.readiness,
        compatibility=result.compatibility,
        warnings=warnings,
        summary=summary,
    )


def list_technologies() -> TechnologyListResponse:
    return TechnologyListResponse(
        milestone_1_platforms=list(MILESTONE_1_PLATFORMS),
        technologies=list_technologies_api(),
    )


def inspect_dataset(req: DatasetInspectRequest) -> DatasetInspectResponse:
    path = _dataset_path(req.dataset_id)
    if path.exists():
        record = json.loads(path.read_text())
        return DatasetInspectResponse(
            dataset_id=req.dataset_id,
            platform=record.get("platform", "unknown"),
            technology_profile=record.get("technology_profile", {}),
            readiness=record.get("readiness", {}),
            compatibility=record.get("compatibility", {}),
            warnings=record.get("warnings", []),
            metadata=record.get("metadata", {}),
        )
    if req.source_path:
        result = ingest_dataset(req.source_path)
        return DatasetInspectResponse(
            dataset_id=result.dataset_id,
            platform=result.platform,
            technology_profile=result.technology_profile,
            readiness=result.readiness,
            compatibility=result.compatibility,
            warnings=result.warnings,
            metadata=result.metadata,
        )
    return DatasetInspectResponse(
        dataset_id=req.dataset_id,
        platform="unknown",
        technology_profile={},
        readiness={"status": "not_found", "score": 0},
        compatibility={},
        warnings=[f"Dataset {req.dataset_id} not found"],
        metadata={},
    )


def dataset_readiness(dataset_id: str) -> DatasetReadinessResponse:
    path = _dataset_path(dataset_id)
    if not path.exists():
        return DatasetReadinessResponse(
            dataset_id=dataset_id,
            readiness={"status": "not_found", "score": 0},
            compatibility={},
            warnings=[f"Dataset {dataset_id} not found"],
        )
    record = json.loads(path.read_text())
    return DatasetReadinessResponse(
        dataset_id=dataset_id,
        readiness=record.get("readiness", {}),
        compatibility=record.get("compatibility", {}),
        warnings=record.get("warnings", []),
    )


def _load_adata_for_dataset(dataset_id: str):
    path = _dataset_path(dataset_id)
    if not path.exists():
        return None, []
    record = json.loads(path.read_text())
    adata_path = record.get("adata_path", "")
    if not adata_path or not Path(adata_path).exists():
        return None, record.get("warnings", []) + ["AnnData path missing — re-upload dataset"]
    import anndata as ad

    return ad.read_h5ad(adata_path), record.get("warnings", [])


def run_workflow(req: WorkflowRunRequest) -> WorkflowRunResponse:
    run = WorkflowRun(
        module=req.module,
        inputs={"params": req.params, "allow_demo": req.allow_demo},
        status="running",
        traceability=WorkflowRun.from_dict(
            {
                "project_id": req.project_id,
                "dataset_id": req.dataset_id,
            }
        ).traceability,
    )
    warnings: List[str] = []
    outputs: Dict[str, Any] = {}
    params = dict(req.params or {})

    try:
        adata, load_warnings = _load_adata_for_dataset(req.dataset_id)
        warnings.extend(load_warnings)

        if req.module == "discovery":
            out = run_discovery_engine(
                adata=adata,
                dataset_id=req.dataset_id,
                allow_demo=req.allow_demo,
                seed=int(params.get("seed", 42)),
            )
            outputs = {
                "status": out.get("status"),
                "findings_count": len(out.get("findings", [])),
                "evidence_count": len(out.get("evidence", [])),
                "is_demo": out.get("is_demo", False),
            }
            run.outputs = to_json_serializable(
                {
                    "findings": out.get("findings", []),
                    "evidence": out.get("evidence", []),
                    "run_id": out.get("run_id"),
                }
            )
            warnings.extend(out.get("warnings", []))
            if out.get("run_id"):
                run.traceability.run_id = str(out["run_id"])
            run.status = out.get("status", "complete")
        elif req.module in ("qc_transformation", "qc_preprocess", "qc"):
            from mbsi.workflows.qc import run_qc_workflow

            record = run_qc_workflow(
                adata,
                min_counts=int(params.get("min_counts", 10)),
                min_genes=int(params.get("min_genes", 200)),
                max_mito_pct=float(params.get("max_mito_pct", 20.0)),
                technology_key=str(params.get("technology_key", "")),
            )
            outputs = record.outputs
            warnings.extend(record.warnings)
            run.status = record.status
            run.outputs = outputs
        elif req.module in ("visualization", "spatial_analysis", "analyze"):
            from mbsi.workflows.analyze import run_analyze_workflow

            record = run_analyze_workflow(adata, params)
            outputs = record.outputs
            warnings.extend(record.warnings)
            run.status = record.status
            run.outputs = outputs
        elif req.module in ("preprocess", "normalization"):
            from mbsi.workflows.preprocess import run_preprocess_workflow

            record = run_preprocess_workflow(adata, technology_key=str(params.get("technology_key", "")))
            outputs = record.outputs
            warnings.extend(record.warnings)
            run.status = record.status
            run.outputs = outputs
        elif req.module == "spatial_variable_genes":
            from mbsi.spatial_stats import spatial_autocorrelation_table

            if adata is None:
                raise ValueError("AnnData required for SVG analysis")
            table = spatial_autocorrelation_table(
                adata,
                n_top=int(params.get("n_top", 500)),
                k=int(params.get("k", 6)),
            )
            outputs = {"svg_table": table.head(50).to_dict(), "n_genes": len(table)}
            run.status = "complete"
            run.outputs = outputs
        elif req.module == "spatial_domains":
            from mbsi.domains import detect_domains

            if adata is None:
                raise ValueError("AnnData required for domain detection")
            _, summary, domain_warnings = detect_domains(
                adata,
                method=str(params.get("method", "leiden")),
                resolution=float(params.get("resolution", 0.8)),
            )
            warnings.extend(domain_warnings)
            outputs = {"domain_summary": summary.to_dict(), "method": params.get("method", "leiden")}
            run.status = "complete"
            run.outputs = outputs
        elif req.module == "phenotyping":
            from mbsi.phenotyping import score_marker_panel, score_tme

            if adata is None:
                raise ValueError("AnnData required for phenotyping")
            panel = str(params.get("panel", "immune"))
            _, panel_summary = score_marker_panel(adata, panel)
            _, tme_summary = score_tme(adata)
            outputs = {
                "panel_summary": panel_summary.to_dict(),
                "tme_summary": tme_summary.to_dict(),
            }
            run.status = "complete"
            run.outputs = outputs
        elif req.module == "report_export":
            from mbsi.workflows.report import run_report_workflow

            out_dir = Path("data/outputs/reports")
            record = run_report_workflow(out_dir, snapshot=params.get("snapshot"), export_type=params.get("export_type", "html"))
            outputs = record.outputs
            warnings.extend(record.warnings)
            run.status = record.status
            run.outputs = outputs
        else:
            run.status = "stub"
            warnings.append(f"Workflow module '{req.module}' handler is a stub — wire to mbsi.workflows")
            outputs = {"module": req.module, "status": "stub"}
            run.outputs = outputs
    except Exception as exc:
        run.status = "failed"
        warnings.append(str(exc))

    run.warnings = warnings
    _RUNS[run.run_id] = run
    registry = ProjectRegistry()
    registry.register_run(
        dataset_id=req.dataset_id,
        finding_ids=[],
        run_id=run.run_id,
        metadata={"module": req.module, "status": run.status},
    )
    return WorkflowRunResponse(
        run_id=run.run_id,
        status=run.status,
        module=run.module,
        outputs=outputs,
        warnings=warnings,
    )


def workflow_status(run_id: str) -> WorkflowStatusResponse:
    run = _RUNS.get(run_id)
    if run is None:
        registry = ProjectRegistry()
        rec = registry.get_run(run_id)
        if rec is None:
            return WorkflowStatusResponse(
                run_id=run_id,
                status="not_found",
                module="",
                outputs={},
                warnings=[f"Run {run_id} not found"],
            )
        return WorkflowStatusResponse(
            run_id=run_id,
            status=rec.get("metadata", {}).get("status", "unknown"),
            module=rec.get("metadata", {}).get("module", ""),
            outputs={"finding_ids": rec.get("finding_ids", [])},
            warnings=[],
        )
    return WorkflowStatusResponse(
        run_id=run.run_id,
        status=run.status,
        module=run.module,
        outputs=run.outputs,
        warnings=run.warnings,
    )


def list_results(dataset_id: str) -> ResultsListResponse:
    registry = ProjectRegistry()
    runs = registry.list_runs(dataset_id=dataset_id)
    results = [
        {
            "run_id": r.get("run_id"),
            "timestamp": r.get("timestamp"),
            "metadata": r.get("metadata", {}),
            "finding_ids": r.get("finding_ids", []),
        }
        for r in runs
    ]
    return ResultsListResponse(dataset_id=dataset_id, results=results)


def list_findings(
    *,
    project_id: str = "",
    dataset_id: str = "",
    run_id: str = "",
) -> FindingsListResponse:
    findings: List[Dict[str, Any]] = []
    if run_id and run_id in _RUNS:
        outputs = _RUNS[run_id].outputs or {}
        findings = list(outputs.get("findings", []))
    return FindingsListResponse(
        project_id=project_id,
        dataset_id=dataset_id,
        run_id=run_id,
        findings=findings,
    )


def list_evidence(
    *,
    project_id: str = "",
    dataset_id: str = "",
    run_id: str = "",
) -> EvidenceListResponse:
    evidence: List[Dict[str, Any]] = []
    if run_id and run_id in _RUNS:
        outputs = _RUNS[run_id].outputs or {}
        evidence = list(outputs.get("evidence", []))
    return EvidenceListResponse(
        project_id=project_id,
        dataset_id=dataset_id,
        run_id=run_id,
        evidence=evidence,
    )


def generate_report(req: ReportGenerateRequest) -> ReportGenerateResponse:
    report_id = str(uuid4())
    project_path = _project_path(req.project_id) if req.project_id else None
    project = (
        ProjectMetadata.from_dict(json.loads(project_path.read_text()))
        if project_path and project_path.exists()
        else ProjectMetadata(title="MBSI Report")
    )
    report = ReportMetadata(
        project=project,
        traceability=ReportMetadata.from_dict(
            {
                "project_id": req.project_id,
                "dataset_id": req.dataset_id,
                "run_id": req.run_id,
            }
        ).traceability,
        report_type=req.report_type,
    )
    if req.run_id:
        findings = list_findings(run_id=req.run_id).findings
        evidence = list_evidence(run_id=req.run_id).evidence
        report.finding_ids = [f.get("finding_id", "") for f in findings]
        report.evidence_ids = [e.get("evidence_id", "") for e in evidence]

    out_dir = Path("data/outputs/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{report_id}.json"
    payload = report.to_dict()
    report_path.write_text(json.dumps(payload, indent=2, default=str))
    report.output_files = [str(report_path)]
    return ReportGenerateResponse(
        report_id=report_id,
        report=payload,
        output_files=report.output_files,
    )
