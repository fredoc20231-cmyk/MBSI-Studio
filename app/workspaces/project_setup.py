"""Deprecated alias — use study_setup; re-exports shared helpers."""

from app.workspaces._study_setup_core import (
    ANALYSIS_ROWS,
    PLATFORM_OPTIONS,
    SAMPLE_COLUMNS,
    STEREO_SEQ_EXPECTED_FILES,
    _build_compatibility_table,
    _compute_dataset_readiness,
    _compute_project_completeness,
    _init_project_state,
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


def render() -> None:
    from app.workspaces.study_setup import render as study_setup_render

    study_setup_render()


__all__ = ["render"]
