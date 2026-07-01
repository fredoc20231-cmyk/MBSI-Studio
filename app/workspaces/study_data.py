"""Study & Data — project setup, experimental design, technology-aware upload."""

from __future__ import annotations

from typing import List

import pandas as pd
import streamlit as st

from app.components.page_header import render_page_header
from app.workspaces._study_setup_core import (
    ANALYSIS_ROWS,
    SAMPLE_COLUMNS,
    _build_compatibility_table,
    _compute_dataset_readiness,
    _compute_project_completeness,
    _init_project_state,
    _render_download_section,
    _render_experimental_design,
    _render_file_upload,
    _render_platform_modality,
    _render_project_description,
    _render_readiness_section,
    _render_sample_table,
    _render_stereo_seq_guidance,
    _render_summary_card,
    _uploaded_file_summary,
)
from mbsi.schema.project import ProjectMetadata
from mbsi.schema.sample import SampleRecord
from mbsi.schema.technology import TECHNOLOGY_CATALOG, UI_TECHNOLOGY_OPTIONS, get_technology
from mbsi.schema.workflow import WorkflowModule
from mbsi.workflows.ingest import run_ingest_workflow


def _render_technology_selection() -> str:
    st.markdown("#### Technology")
    labels = [label for label, _ in UI_TECHNOLOGY_OPTIONS]
    keys = [key for _, key in UI_TECHNOLOGY_OPTIONS]
    current = st.session_state.get("selected_technology", "")
    idx = keys.index(current) if current in keys else 0
    choice = st.selectbox(
        "Spatial technology",
        labels,
        index=idx,
        key="sd_technology_select",
        help="Technology drives required files, QC hints, and module compatibility",
    )
    tech_key = dict(UI_TECHNOLOGY_OPTIONS)[choice]
    st.session_state.selected_technology = tech_key
    st.session_state.mbsi_platform = tech_key

    spec = get_technology(tech_key)
    if spec:
        with st.expander(f"{spec.label} — file requirements", expanded=True):
            st.markdown("**Required files**")
            for req in spec.required_files:
                st.markdown(f"- {req}")
            if spec.optional_files:
                st.markdown("**Optional files**")
                for opt in spec.optional_files:
                    st.markdown(f"- {opt}")
            st.markdown(f"**Normalization:** {spec.normalization_strategy}")
            st.markdown(f"**Segmentation:** {spec.segmentation_logic}")
            if spec.notes:
                st.caption(spec.notes)
    plat = st.session_state.platform_metadata
    plat["platforms"] = [choice]
    st.session_state.platform_metadata = plat
    return tech_key


def _schema_samples() -> List[SampleRecord]:
    samples = st.session_state.get("sample_metadata")
    if isinstance(samples, pd.DataFrame):
        rows = samples.to_dict("records")
    elif isinstance(samples, list):
        rows = samples
    else:
        rows = []
    return SampleRecord.from_rows(rows)


def render() -> None:
    _init_project_state()
    render_page_header(
        "Study & Data",
        "Define project, experimental design, samples, upload files, review readiness.",
        icon="📁",
    )

    if st.session_state.get("using_synthetic_demo") and st.session_state.get("adata") is not None:
        st.info("Sample Dataset Loaded — labeled demo data for exploration on this page only.")

    tech_key = _render_technology_selection()
    st.divider()
    _render_project_description()
    st.divider()
    _render_experimental_design()
    st.divider()
    _render_sample_table()
    st.divider()
    _render_platform_modality()
    _render_stereo_seq_guidance()
    st.divider()
    _render_download_section()
    st.divider()
    _render_file_upload()
    st.divider()

    project_score, project_missing = _compute_project_completeness()
    dataset_score, _ = _compute_dataset_readiness()
    compatibility_df = _build_compatibility_table()
    recommended = _render_readiness_section(project_score, dataset_score, project_missing, compatibility_df)

    project = ProjectMetadata.from_session(st.session_state.get("project_metadata"))
    samples = _schema_samples()
    ingestion = st.session_state.get("ingestion_result")
    run = run_ingest_workflow(
        project=project,
        samples=samples,
        files=_uploaded_file_summary(),
        adata=st.session_state.get("adata"),
        ingestion=ingestion,
        technology_key=tech_key,
        project_score=float(project_score),
        dataset_score=float(dataset_score),
    )
    st.session_state.run_outputs["study_data"] = run.to_dict()

    st.divider()
    _render_summary_card(recommended, compatibility_df, _uploaded_file_summary())

    if st.button("Continue to QC & Transformation", type="primary", key="sd_continue_qc"):
        st.session_state.active_module = WorkflowModule.QC_TRANSFORMATION.value
        st.rerun()

    st.session_state.mbsi_readiness = {
        **(st.session_state.get("mbsi_readiness") or {}),
        "project_metadata": dict(st.session_state.get("project_metadata", {})),
        "experimental_design": dict(st.session_state.get("experimental_design", {})),
        "platform_metadata": dict(st.session_state.get("platform_metadata", {})),
        "sample_metadata": (
            st.session_state.sample_metadata.to_dict("records")
            if isinstance(st.session_state.get("sample_metadata"), pd.DataFrame)
            else st.session_state.get("sample_metadata")
        ),
        "technology_key": tech_key,
        "technology_spec": TECHNOLOGY_CATALOG.get(tech_key).to_dict() if tech_key in TECHNOLOGY_CATALOG else {},
        "experimental_target": st.session_state.get("project_metadata", {}).get("experimental_target", ""),
        "hypothesis": st.session_state.get("project_metadata", {}).get("hypothesis", ""),
        "stereo_seq_readiness": st.session_state.get("stereo_seq_readiness"),
        "stereo_seq_profile": st.session_state.get("stereo_seq_profile"),
        "project_completeness": project_score,
        "dataset_readiness": dataset_score,
    }
