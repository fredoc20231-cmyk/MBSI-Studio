"""Header status helpers — dataset, run, technology, project labels."""

from __future__ import annotations

from typing import Tuple

import streamlit as st


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


def get_dataset_status() -> Tuple[str, str]:
    """Return (label, css_class) for header dataset status chip."""
    wf_state = _workflow_state()
    if wf_state in {"running", "processing", "in_progress", "queued"}:
        return "Processing", "saas-status-warn"

    adata = st.session_state.get("adata")
    if adata is None:
        return "No Dataset Loaded", "saas-status-warn"

    readiness = st.session_state.get("mbsi_readiness") or {}
    ingestion = st.session_state.get("ingestion_result") or {}

    validated = bool(
        readiness.get("validated")
        or str(readiness.get("status", "")).lower() in {"validated", "ready", "complete"}
        or float(readiness.get("dataset_readiness") or 0) >= 70
        or float(ingestion.get("readiness_score") or 0) >= 70
    )

    if wf_state in {"complete", "completed", "success", "done"}:
        return "Complete", "saas-status-ok"
    if validated:
        return "Dataset Validated", "saas-status-ok"
    return "Dataset Loaded", "saas-status-ok"


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
