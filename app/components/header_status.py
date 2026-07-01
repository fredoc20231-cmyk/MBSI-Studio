"""Header status helpers — dataset, run, technology, project labels."""

from __future__ import annotations

from typing import Tuple

import streamlit as st

DATASET_STATUSES = ("UNVERIFIED", "VALIDATING", "READY", "CORRUPTED")


def _workflow_state() -> str:
    wf = st.session_state.get("workflow_status") or {}
    return str(wf.get("status") or wf.get("state") or "").lower()


def get_project_label() -> str:
    meta = st.session_state.get("project_metadata") or {}
    title = meta.get("title") or meta.get("name") or ""
    if title:
        return str(title)
    return str(st.session_state.get("project_name") or "No project loaded")


def get_technology_label() -> str:
    tech_key = st.session_state.get("selected_technology") or st.session_state.get("mbsi_platform") or ""
    if not tech_key:
        return "Not selected"
    try:
        from mbsi.schema.technology import get_technology

        spec = get_technology(tech_key)
        if spec:
            return spec.label
    except Exception:
        pass
    return str(tech_key).replace("_", " ").title()


def _is_corrupted(
    wf_state: str,
    readiness: dict,
    ingestion: dict,
    validators: dict,
) -> bool:
    if wf_state in {"failed", "error", "corrupted"}:
        return True
    status = str(readiness.get("status", "")).lower()
    if status in {"corrupted", "error", "failed"}:
        return True
    if ingestion.get("corrupted") or validators.get("failed"):
        return True
    if validators.get("errors"):
        return True
    return False


def _is_validating(wf_state: str, readiness: dict) -> bool:
    if wf_state in {"running", "processing", "in_progress", "queued", "validating"}:
        return True
    if str(readiness.get("status", "")).lower() == "validating":
        return True
    job = st.session_state.get("job_status") or {}
    if str(job.get("status", "")).lower() in {"running", "queued", "validating"}:
        return True
    return False


def _is_ready(adata, readiness: dict, ingestion: dict, validators: dict) -> bool:
    if adata is None:
        return False
    if validators.get("passed") or validators.get("valid"):
        return True
    if readiness.get("validated"):
        return True
    status = str(readiness.get("status", "")).lower()
    if status in {"validated", "ready", "complete"}:
        return True
    score = float(readiness.get("dataset_readiness") or ingestion.get("readiness_score") or 0)
    return score >= 70


def get_dataset_status() -> Tuple[str, str]:
    """Return (label, css_class) for header dataset status chip.

    Status values: UNVERIFIED | VALIDATING | READY | CORRUPTED
    """
    wf_state = _workflow_state()
    adata = st.session_state.get("adata")
    readiness = st.session_state.get("mbsi_readiness") or {}
    ingestion = st.session_state.get("ingestion_result") or {}
    validators = st.session_state.get("validators") or {}

    if _is_corrupted(wf_state, readiness, ingestion, validators):
        return "CORRUPTED", "saas-status-error"
    if _is_validating(wf_state, readiness):
        return "VALIDATING", "saas-status-warn"
    if adata is None:
        return "UNVERIFIED", "saas-status-warn"
    if _is_ready(adata, readiness, ingestion, validators):
        return "READY", "saas-status-ok"
    return "UNVERIFIED", "saas-status-neutral"


def get_run_status() -> Tuple[str, str]:
    """Return (label, css_class) for header run status chip."""
    wf = st.session_state.get("workflow_status") or {}
    wf_state = _workflow_state()
    wf_module = wf.get("module") or wf.get("name") or ""

    if wf_state in {"running", "processing", "in_progress"}:
        label = f"Running{f' · {wf_module}' if wf_module else ''}"
        return label, "saas-status-warn"
    if wf_state in {"complete", "completed", "success", "done"}:
        label = f"Complete{f' · {wf_module}' if wf_module else ''}"
        return label, "saas-status-ok"
    if wf_state in {"failed", "error"}:
        return "Failed", "saas-status-error"

    last = str(st.session_state.get("last_run") or "").strip()
    if last:
        return last[:48], "saas-status-neutral"
    return "Idle", "saas-status-neutral"
