"""Shared study setup helpers — project metadata, samples, upload, readiness."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from app.components.interactive_figures import render_interactive_plot
from app.components.page_utils import load_advanced_demo_into_session
from app.components.uploaders import data_readiness_score
from app.workspaces._helpers import safe_register_finding
from app.workspaces._sample_upload_state import (
    apply_ingestion_to_session,
    can_start_analysis,
    get_primary_ingested_sample,
    ingest_sample_file,
    required_files_for_technology,
    resolve_sample_technology,
    status_label,
    sync_sample_uploads,
    upload_file_types_for_technology,
)
from app.workspaces._upload_helpers import _render_detection_panel, _store_ingestion
from mbsi.io.ingest import save_upload_to_temp
from mbsi.io.compatibility import get_compatibility_matrix, recommended_next_step_for_module
from mbsi.profiles.stereo_seq import get_stereo_seq_profile
from mbsi.schema.technology import UI_TECHNOLOGY_OPTIONS, get_technology, is_milestone_platform
from mbsi.schema.workflow import WorkflowModule
from mbsi.visualization.analysis_plots import plot_qc_spatial

STUDY_TYPES = [
    "Case-control",
    "Treatment response",
    "Longitudinal",
    "Single-arm cohort",
    "Exploratory / discovery",
    "Other",
]
REPLICATE_TYPES = ["Biological", "Technical", "Both", "None", "Unknown"]
ORGANISMS = ["Human", "Mouse", "Other"]
PLATFORM_OPTIONS = [label for label, _ in UI_TECHNOLOGY_OPTIONS]

STEREO_SEQ_EXPECTED_FILES = [
    "Expression matrix (GEF/CGEF)",
    "Coordinates",
    "Registered image",
    "Tissue segmentation",
    "Cell segmentation",
    "Region annotations",
    "StereoMap outputs",
    "SAW outputs",
    "QC reports (HTML)",
]
MODALITY_OPTIONS = [
    "Transcriptomics",
    "Proteomics (CODEX/IMC)",
    "ATAC-seq",
    "Multi-omic",
    "Histology only",
    "Mutation/CNV",
]
SAMPLE_COLUMNS = [
    "sample_id",
    "sample_name",
    "patient_id",
    "condition",
    "timepoint",
    "replicate_id",
    "batch_id",
    "technology",
    "file_name",
    "tissue_region",
    "notes",
]
ANALYSIS_ROWS = [
    ("Study & Data", WorkflowModule.STUDY_DATA.value),
    ("QC & Transformation", WorkflowModule.QC_TRANSFORMATION.value),
    ("Visualization", WorkflowModule.VISUALIZATION.value),
    ("Spatial Variable Genes", WorkflowModule.SPATIAL_VARIABLE_GENES.value),
    ("Spatial Domains", WorkflowModule.SPATIAL_DOMAINS.value),
    ("Differential Analysis", WorkflowModule.DIFFERENTIAL_ANALYSIS.value),
    ("Segmentation & Registration", WorkflowModule.SEGMENT_REGISTER.value),
    ("MBSI Reconstruction", WorkflowModule.RECONSTRUCTION.value),
    ("Benchmark", WorkflowModule.BENCHMARK.value),
    ("Discovery Intelligence", WorkflowModule.DISCOVERY.value),
    ("AI Review", WorkflowModule.AI_REVIEW.value),
    ("Report & Export", WorkflowModule.REPORT_EXPORT.value),
]


def _init_project_state() -> None:
    st.session_state.setdefault(
        "project_metadata",
        {
            "project_title": "",
            "sample_name": "",
            "disease_context": "",
            "biological_question": "",
            "experimental_target": "",
            "hypothesis": "",
            "study_objective": "",
            "organism": "Human",
            "therapeutic_context": "",
        },
    )
    st.session_state.setdefault(
        "experimental_design",
        {
            "study_type": STUDY_TYPES[0],
            "num_samples": 3,
            "has_replicates": "Not sure",
            "replicate_type": REPLICATE_TYPES[0],
            "comparison_groups": "",
            "timepoints": "",
            "treatment_arms": "",
            "primary_comparison": "",
            "secondary_comparisons": "",
            "patient_ids": "",
            "batch_ids": "",
            "paired_design": "No",
            "controls": "",
        },
    )
    st.session_state.setdefault("platform_metadata", {"platforms": [], "modalities": []})
    st.session_state.setdefault("clinical_metadata", None)
    st.session_state.setdefault("project_completeness", 0)
    st.session_state.setdefault("dataset_readiness", 0)
    st.session_state.setdefault("dataset_compatibility", [])
    st.session_state.setdefault("download_manifest", None)
    st.session_state.setdefault("download_dir", None)
    st.session_state.setdefault("dataset_platform", None)
    st.session_state.setdefault("parsed_download_urls", [])


def _default_sample_rows(num_samples: int) -> pd.DataFrame:
    tech_key = st.session_state.get("selected_technology", "")
    tech_label = next((label for label, key in UI_TECHNOLOGY_OPTIONS if key == tech_key), PLATFORM_OPTIONS[0])
    rows = []
    for i in range(1, max(1, num_samples) + 1):
        rows.append(
            {
                "sample_id": f"S{i}",
                "sample_name": f"Sample {i}",
                "patient_id": f"P{i:03d}",
                "condition": "Case" if i % 2 else "Control",
                "timepoint": "Baseline",
                "replicate_id": "R1",
                "batch_id": "batch1",
                "technology": tech_label,
                "file_name": "",
                "tissue_region": "Tumor core",
                "notes": "",
            }
        )
    return pd.DataFrame(rows, columns=SAMPLE_COLUMNS)


def _sync_sample_table(num_samples: int) -> pd.DataFrame:
    current = st.session_state.get("sample_metadata")
    if not isinstance(current, pd.DataFrame) or current.empty:
        df = _default_sample_rows(num_samples)
        st.session_state.sample_metadata = df
    elif len(current) != num_samples:
        preserved = current.head(num_samples).copy()
        if len(preserved) < num_samples:
            extra = _default_sample_rows(num_samples - len(preserved))
            extra["sample_id"] = [f"S{i}" for i in range(len(preserved) + 1, num_samples + 1)]
            preserved = pd.concat([preserved, extra], ignore_index=True)
        st.session_state.sample_metadata = preserved.reset_index(drop=True)

    tech_key = st.session_state.get("selected_technology", "")
    st.session_state.sample_uploads = sync_sample_uploads(
        st.session_state.sample_metadata,
        st.session_state.get("sample_uploads"),
        tech_key,
    )
    return st.session_state.sample_metadata


def _render_project_description() -> None:
    st.markdown("#### Project description")
    meta = st.session_state.project_metadata
    c1, c2 = st.columns(2)
    meta["project_title"] = c1.text_input(
        "Project title",
        value=meta.get("project_title", ""),
        placeholder="e.g. HGSOC spatial response to PARP inhibition",
        key="ps_project_title",
    )
    meta["disease_context"] = c2.text_input(
        "Disease / indication context",
        value=meta.get("disease_context", ""),
        placeholder="e.g. High-grade serous ovarian cancer, FIGO III-IV",
        key="ps_disease_context",
    )
    meta["biological_question"] = st.text_area(
        "Biological question",
        value=meta.get("biological_question", ""),
        placeholder="What spatial biology question does this study address?",
        key="ps_biological_question",
    )
    meta["experimental_target"] = st.text_input(
        "Experimental target",
        value=meta.get("experimental_target", ""),
        placeholder="e.g. PARP1, PD-L1, TME remodeling",
        key="ps_experimental_target",
        help="Critical for AI review grounding",
    )
    meta["hypothesis"] = st.text_area(
        "Hypothesis",
        value=meta.get("hypothesis", ""),
        placeholder="Primary hypothesis for spatial analysis and AI review",
        key="ps_hypothesis",
    )
    meta["study_objective"] = st.text_area(
        "Study objective",
        value=meta.get("study_objective", ""),
        placeholder="Primary endpoints and hypotheses for spatial analysis",
        key="ps_study_objective",
    )
    c3, c4 = st.columns(2)
    org_idx = ORGANISMS.index(meta.get("organism", "Human")) if meta.get("organism") in ORGANISMS else 0
    meta["organism"] = c3.selectbox("Organism", ORGANISMS, index=org_idx, key="ps_organism")
    meta["therapeutic_context"] = c4.text_input(
        "Therapeutic context",
        value=meta.get("therapeutic_context", ""),
        placeholder="e.g. Post-neoadjuvant chemotherapy, IO combination arm",
        key="ps_therapeutic_context",
    )
    st.session_state.project_metadata = meta
    if meta.get("project_title"):
        st.session_state.project_name = meta["project_title"]


def _render_experimental_design() -> None:
    st.markdown("#### Experimental design")
    design = st.session_state.experimental_design
    c1, c2, c3 = st.columns(3)
    st_idx = STUDY_TYPES.index(design.get("study_type", STUDY_TYPES[0]))
    if design.get("study_type") not in STUDY_TYPES:
        st_idx = 0
    design["study_type"] = c1.selectbox("Study type", STUDY_TYPES, index=st_idx, key="ps_study_type")
    design["num_samples"] = int(
        c2.number_input(
            "Number of samples",
            min_value=1,
            max_value=500,
            value=int(design.get("num_samples", 3)),
            key="ps_num_samples",
        )
    )
    rep_opts = ["Yes", "No", "Not sure"]
    rep_idx = rep_opts.index(design.get("has_replicates", "Not sure")) if design.get("has_replicates") in rep_opts else 2
    design["has_replicates"] = c3.radio("Replicates?", rep_opts, index=rep_idx, horizontal=True, key="ps_has_replicates")
    c4, c5 = st.columns(2)
    rt_idx = REPLICATE_TYPES.index(design.get("replicate_type", REPLICATE_TYPES[0]))
    if design.get("replicate_type") not in REPLICATE_TYPES:
        rt_idx = 0
    design["replicate_type"] = c4.selectbox("Replicate type", REPLICATE_TYPES, index=rt_idx, key="ps_replicate_type")
    design["comparison_groups"] = c5.text_area(
        "Comparison groups",
        value=design.get("comparison_groups", ""),
        placeholder="e.g. Responder vs non-responder; Treatment A vs B",
        key="ps_comparison_groups",
    )
    c6, c7 = st.columns(2)
    design["primary_comparison"] = c6.text_input(
        "Primary comparison",
        value=design.get("primary_comparison", ""),
        placeholder="e.g. Responder vs non-responder",
        key="ps_primary_comparison",
    )
    design["secondary_comparisons"] = c7.text_input(
        "Secondary comparisons (comma-separated)",
        value=design.get("secondary_comparisons", ""),
        placeholder="e.g. Treatment A vs B, Baseline vs post-treatment",
        key="ps_secondary_comparisons",
    )
    c8, c9 = st.columns(2)
    design["timepoints"] = c8.text_input(
        "Timepoints (comma-separated)",
        value=design.get("timepoints", ""),
        placeholder="e.g. Baseline, Week 4, Week 12",
        key="ps_timepoints",
    )
    design["treatment_arms"] = c9.text_input(
        "Treatment arms (comma-separated)",
        value=design.get("treatment_arms", ""),
        placeholder="e.g. Arm A: PARP inhibitor, Arm B: placebo",
        key="ps_treatment_arms",
    )
    design["patient_ids"] = st.text_input(
        "Patient / animal IDs (comma-separated, optional)",
        value=design.get("patient_ids", ""),
        placeholder="e.g. P001, P002, P003 — or leave blank and fill sample table",
        key="ps_patient_ids",
    )
    c10, c11 = st.columns(2)
    design["batch_ids"] = c10.text_input(
        "Batch IDs (comma-separated)",
        value=design.get("batch_ids", ""),
        placeholder="e.g. batch1, batch2",
        key="ps_batch_ids",
    )
    paired_opts = ["No", "Yes — patient-matched", "Yes — sample-matched"]
    design["paired_design"] = c11.selectbox(
        "Paired design",
        paired_opts,
        index=paired_opts.index(design.get("paired_design", "No")) if design.get("paired_design") in paired_opts else 0,
        key="ps_paired_design",
    )
    design["controls"] = st.text_input(
        "Controls",
        value=design.get("controls", ""),
        placeholder="e.g. Vehicle, untreated, normal tissue",
        key="ps_controls",
    )
    st.session_state.experimental_design = design


def _render_sample_table() -> None:
    st.markdown("#### Sample metadata table")
    num_samples = int(st.session_state.experimental_design.get("num_samples", 3))
    df = _sync_sample_table(num_samples)
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        key="ps_sample_editor",
        column_config={
            "sample_id": st.column_config.TextColumn("Sample ID", required=True),
            "sample_name": st.column_config.TextColumn("Sample name"),
            "patient_id": st.column_config.TextColumn("Patient ID"),
            "condition": st.column_config.TextColumn("Condition"),
            "timepoint": st.column_config.TextColumn("Timepoint"),
            "replicate_id": st.column_config.TextColumn("Replicate"),
            "batch_id": st.column_config.TextColumn("Batch ID"),
            "technology": st.column_config.SelectboxColumn("Technology", options=PLATFORM_OPTIONS),
            "file_name": st.column_config.TextColumn("File name"),
            "tissue_region": st.column_config.TextColumn("Tissue region"),
            "notes": st.column_config.TextColumn("Notes"),
        },
    )
    st.session_state.sample_metadata = edited
    tech_key = st.session_state.get("selected_technology", "")
    st.session_state.sample_uploads = sync_sample_uploads(
        edited,
        st.session_state.get("sample_uploads"),
        tech_key,
    )


def _update_sample_metadata_file_name(sample_id: str, file_name: str) -> None:
    samples = st.session_state.get("sample_metadata")
    if not isinstance(samples, pd.DataFrame) or samples.empty:
        return
    mask = samples["sample_id"].astype(str) == str(sample_id)
    if mask.any():
        samples.loc[mask, "file_name"] = file_name
        st.session_state.sample_metadata = samples


def _render_per_sample_upload_cards() -> None:
    """One upload card per sample row — Milestone 1 Visium/Xenium/Generic."""
    samples = st.session_state.get("sample_metadata")
    if not isinstance(samples, pd.DataFrame) or samples.empty:
        st.info("Add samples in the metadata table above before uploading data.")
        return

    global_tech = st.session_state.get("selected_technology", "")
    uploads = st.session_state.get("sample_uploads") or {}
    num_samples = int(st.session_state.experimental_design.get("num_samples", len(samples)))

    for _, row in samples.iterrows():
        sample_id = str(row.get("sample_id", "")).strip()
        if not sample_id:
            continue

        tech_key = resolve_sample_technology(row.get("technology"), global_tech)
        upload = uploads.get(sample_id) or {
            "sample_id": sample_id,
            "technology": tech_key,
            "status": "not_uploaded",
        }
        req_files = required_files_for_technology(tech_key)
        file_types = upload_file_types_for_technology(tech_key)

        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(
                f"**{sample_id}** — {row.get('sample_name', '')} · "
                f"{row.get('condition', '—')} · {row.get('technology', tech_key)}"
            )
            c2.markdown(f"**Status:** {status_label(upload.get('status', 'not_uploaded'))}")

            st.caption("Required: " + "; ".join(req_files))
            if upload.get("uploaded_file_name"):
                st.caption(f"File: `{upload['uploaded_file_name']}`")
            for w in upload.get("warnings") or []:
                st.warning(w)

            uploaded = st.file_uploader(
                f"Upload data for {sample_id}",
                type=file_types,
                key=f"ps_sample_upload_{sample_id}",
            )
            if uploaded is not None:
                suffix = Path(uploaded.name).suffix.lower() or ".bin"
                temp_path = save_upload_to_temp(uploaded, suffix)
                result = ingest_sample_file(
                    temp_path,
                    sample_id=sample_id,
                    technology_key=tech_key,
                    uploaded_file_name=uploaded.name,
                )
                patch = {k: v for k, v in result.items() if k != "adata"}
                st.session_state.sample_uploads[sample_id] = patch
                _update_sample_metadata_file_name(sample_id, uploaded.name)

                session_updates = apply_ingestion_to_session(result, num_samples=num_samples)
                if "adata" in session_updates:
                    st.session_state.adata = session_updates["adata"]
                if "ingestion_result" in session_updates:
                    st.session_state.ingestion_result = session_updates["ingestion_result"]
                if "mbsi_platform" in session_updates:
                    st.session_state.mbsi_platform = session_updates["mbsi_platform"]
                if "using_synthetic_demo" in session_updates:
                    st.session_state.using_synthetic_demo = session_updates["using_synthetic_demo"]
                if "sample_adatas" in session_updates:
                    st.session_state.sample_adatas = {
                        **(st.session_state.get("sample_adatas") or {}),
                        **session_updates["sample_adatas"],
                    }
                if "sample_adata_paths" in session_updates:
                    st.session_state.sample_adata_paths = {
                        **(st.session_state.get("sample_adata_paths") or {}),
                        **session_updates["sample_adata_paths"],
                    }

                if result.get("status") == "ingested":
                    from app.components.notification_center import push_notification

                    adata = result.get("adata")
                    n_obs = adata.n_obs if adata is not None else "?"
                    push_notification(
                        f"Sample {sample_id} ingested ({n_obs} observations).",
                        title="Sample ingest complete",
                        level="success",
                        source="study_data",
                    )
                    st.success(f"{sample_id}: ingested {uploaded.name}")
                else:
                    st.error(f"{sample_id}: ingest failed — see warnings above.")
                st.rerun()


def _ensure_primary_adata_from_uploads() -> None:
    """Set global adata from first ingested sample when missing."""
    if st.session_state.get("adata") is not None:
        return
    uploads = st.session_state.get("sample_uploads") or {}
    sid, upload = get_primary_ingested_sample(uploads)
    if not sid or not upload.get("adata_path"):
        return
    try:
        import anndata as ad

        st.session_state.adata = ad.read_h5ad(upload["adata_path"])
        st.session_state.mbsi_platform = upload.get("platform") or upload.get("technology")
        st.session_state.ingestion_result = {
            "platform": upload.get("platform") or upload.get("technology"),
            "readiness": upload.get("readiness", {}),
            "compatibility": upload.get("compatibility", {}),
            "sample_id": sid,
            "source": upload.get("adata_path"),
        }
    except Exception:
        pass


def _render_start_analysis_button(tech_key: str) -> None:
    """Bottom-of-page Start Analysis — runs Milestone 1 pipeline on primary ingested sample."""
    _ensure_primary_adata_from_uploads()
    enabled, missing = can_start_analysis(
        st.session_state.get("project_metadata"),
        st.session_state.get("sample_metadata"),
        st.session_state.get("sample_uploads"),
        tech_key,
    )
    if missing and not enabled:
        st.caption("Start Analysis requires: " + ", ".join(missing))

    if st.button(
        "Start Analysis",
        type="primary",
        key="sd_start_analysis",
        disabled=not enabled,
    ):
        from pathlib import Path

        from app.components.notification_center import push_notification
        from app.components.page_utils import OUTPUT_DIR
        from mbsi.workflows.milestone1_pipeline import run_milestone1_pipeline

        adata = st.session_state.get("adata")
        if adata is None:
            st.error("No ingested AnnData available.")
            return

        platform = tech_key or st.session_state.get("mbsi_platform") or "generic_h5ad"
        out_dir = Path(OUTPUT_DIR) / "milestone1_pipeline" / platform
        result = run_milestone1_pipeline(
            adata,
            params={
                "platform": platform,
                "output_dir": out_dir,
                "min_counts": 50,
                "min_genes": 10,
            },
        )

        st.session_state.adata = result["adata"]
        st.session_state.analysis_results = {
            k: v for k, v in result.items() if k != "adata"
        }
        st.session_state.marker_table = result.get("markers")
        st.session_state.spatial_stats = result.get("spatial", {}).get("spatial_stats")
        st.session_state.run_outputs["milestone1_pipeline"] = result.get("output_paths", {})
        st.session_state.workflow_status = {
            **(st.session_state.get("workflow_status") or {}),
            "milestone1": result.get("status", "success"),
            "platform": platform,
        }
        st.session_state.last_run = "Milestone 1 analysis"
        st.session_state.active_module = "qc_transformation"

        push_notification(
            f"Milestone 1 pipeline complete — {result['clusters'].get('n_clusters', 0)} clusters.",
            title="Analysis started",
            level="success",
            source="study_data",
        )
        st.rerun()


def _render_platform_modality() -> None:
    st.markdown("#### Platform & modality")
    plat = st.session_state.platform_metadata
    c1, c2 = st.columns(2)
    plat["platforms"] = c1.multiselect(
        "Spatial platforms",
        PLATFORM_OPTIONS,
        default=plat.get("platforms") or [],
        key="ps_platforms",
    )
    plat["modalities"] = c2.multiselect(
        "Data modalities",
        MODALITY_OPTIONS,
        default=plat.get("modalities") or [],
        key="ps_modalities",
    )
    st.session_state.platform_metadata = plat


def _render_stereo_seq_guidance() -> None:
    tech_key = st.session_state.get("selected_technology") or st.session_state.get("mbsi_platform")
    selected = st.session_state.platform_metadata.get("platforms") or []
    is_stereo = tech_key == "stereo_seq" or any("Stereo-seq" in p for p in selected)
    if not is_stereo:
        return
    st.markdown("**STOmics Stereo-seq — expected files**")
    tech = get_technology("stereo_seq")
    if tech:
        st.caption(tech.notes)
    for item in STEREO_SEQ_EXPECTED_FILES:
        st.markdown(f"- {item}")
    profile = get_stereo_seq_profile("bin")
    st.caption(f"Default pipeline: {' → '.join(s['label'] for s in profile['active_pipeline'])}")
    scale = st.selectbox(
        "Analysis scale",
        profile["selectable_scales"],
        format_func=lambda s: profile["ui_hints"].get(s, s),
        key="ps_stereo_scale",
    )
    st.session_state.stereo_seq_profile = get_stereo_seq_profile(scale)


def _upload_csv_metadata(label: str, key: str, session_key: str) -> None:
    uploaded = st.file_uploader(label, type=["csv"], key=key)
    if uploaded is None:
        return
    try:
        df = pd.read_csv(uploaded)
        st.session_state[session_key] = df
        st.success(f"Loaded {len(df)} rows from {uploaded.name}")
        if session_key == "clinical_metadata":
            return
        if set(SAMPLE_COLUMNS).issubset(df.columns):
            st.session_state.sample_metadata = df[SAMPLE_COLUMNS].copy()
            st.session_state.experimental_design["num_samples"] = len(df)
        else:
            st.info("CSV loaded; merge columns manually into the sample table if needed.")
    except Exception as exc:
        st.error(f"Could not load CSV: {exc}")


def _upload_unprocessed(label: str, key: str, session_key: str, file_types: List[str]) -> None:
    uploaded = st.file_uploader(label, type=file_types, key=key)
    if uploaded is None:
        return
    try:
        if uploaded.name.lower().endswith(".csv"):
            st.session_state[session_key] = pd.read_csv(uploaded)
        else:
            st.session_state[session_key] = {"filename": uploaded.name, "size_bytes": uploaded.size}
        st.success(f"Uploaded {uploaded.name}")
        st.caption("Uploaded but downstream processing not yet enabled.")
    except Exception as exc:
        st.error(f"Upload failed: {exc}")


def _render_download_section() -> None:
    """Download from facility / public source — parse URLs, download, inspect, preview."""
    from mbsi.io.downloader.inspector import inspect_downloaded_files, update_ingestion_readiness
    from mbsi.io.downloader.manager import (
        cancel_download_job,
        create_download_job,
        start_download_job_async,
    )
    from mbsi.io.downloader.manifest import load_manifest, manifest_path
    from mbsi.io.downloader.parse_commands import parse_url_entries
    from mbsi.io.downloader.patch_analyzer import run_patch_preview_analysis
    from mbsi.io.ingest import load_dataset_from_manifest
    from app.workspaces._upload_helpers import _store_ingestion

    st.markdown("#### Download from Facility / Public Source")
    st.caption(
        "Paste curl, wget, or raw URLs from your sequencing facility or public repository. "
        "URLs are parsed only — commands are never executed in a shell."
    )

    paste_key = "ss_download_paste"
    default_text = st.session_state.get(paste_key, "")
    pasted = st.text_area(
        "curl / wget / URL list",
        value=default_text,
        height=140,
        placeholder=(
            "curl -L -o WTA_Preview_outs.zip https://cf.10xgenomics.com/...\n"
            "wget https://example.org/gene_groups.csv\n"
            "https://example.org/he_image.ome.tif"
        ),
        key=paste_key,
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    if c1.button("Parse URLs", key="ss_dl_parse"):
        entries = parse_url_entries(pasted)
        st.session_state.parsed_download_urls = entries
        if entries:
            st.success(f"Parsed {len(entries)} URL(s)")
        else:
            st.warning("No URLs found in pasted text")

    parsed = st.session_state.get("parsed_download_urls") or []
    if parsed:
        df = pd.DataFrame(
            [
                {
                    "filename": e.get("filename"),
                    "source": e.get("source"),
                    "role": e.get("likely_role"),
                    "tech_hint": e.get("technology_hint"),
                    "url": e.get("url", "")[:80] + ("…" if len(e.get("url", "")) > 80 else ""),
                }
                for e in parsed
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

    project_id = (
        st.session_state.get("project_metadata", {}).get("project_title")
        or st.session_state.get("project_name")
        or "default_project"
    )

    if c2.button("Start Download", type="primary", key="ss_dl_start", disabled=not parsed):
        from pathlib import Path

        base = Path("data/downloads") / str(project_id).replace(" ", "_")[:40]
        manifest = create_download_job(project_id, pasted, base, parsed_entries=parsed)
        st.session_state.download_manifest = manifest.to_dict()
        st.session_state.download_dir = manifest.output_dir
        start_download_job_async(manifest)
        st.session_state.download_job_id = manifest.job_id
        st.info(f"Download job {manifest.job_id} started in background")

    manifest_dict = st.session_state.get("download_manifest")
    job_id = st.session_state.get("download_job_id")
    if manifest_dict and job_id:
        mp = manifest_path(Path(manifest_dict.get("output_dir", "data/downloads")), job_id)
        if mp.exists():
            try:
                live = load_manifest(mp)
                manifest_dict = live.to_dict()
                st.session_state.download_manifest = manifest_dict
            except Exception:
                pass

    if c3.button("Pause / Cancel", key="ss_dl_cancel", disabled=not job_id):
        if cancel_download_job(job_id):
            st.warning("Cancellation requested — in-progress files may finish current chunk")
        else:
            st.caption("No active background job to cancel")

    if c4.button("Resume", key="ss_dl_resume", disabled=not manifest_dict):
        if manifest_dict:
            from mbsi.io.downloader.manifest import DownloadManifest

            m = DownloadManifest.from_dict(manifest_dict)
            m.status = "queued"
            for u in m.urls:
                if u.status in ("failed", "cancelled", "running"):
                    u.status = "queued"
            start_download_job_async(m)
            st.session_state.download_job_id = m.job_id
            st.info("Resuming incomplete downloads")

    if c5.button("Inspect Files", key="ss_dl_inspect", disabled=not st.session_state.get("download_dir")):
        dl_dir = st.session_state.download_dir
        detection = inspect_downloaded_files(dl_dir)
        bundle = update_ingestion_readiness(dl_dir, detection)
        st.session_state.dataset_platform = detection.get("platform")
        st.session_state.dataset_readiness = bundle["readiness"]
        st.session_state.dataset_compatibility = bundle["compatibility"]
        if manifest_dict:
            manifest_dict["detected_platform"] = detection.get("platform")
            manifest_dict["readiness"] = bundle["readiness"]
            manifest_dict["compatibility"] = bundle["compatibility"]
            st.session_state.download_manifest = manifest_dict
        st.success(f"Platform: {detection.get('platform')} ({detection.get('confidence', 0):.0%} confidence)")

    if c6.button("Run Patch Preview", key="ss_dl_preview", disabled=not st.session_state.get("download_dir")):
        preview = run_patch_preview_analysis(st.session_state.download_dir)
        if manifest_dict:
            manifest_dict["preview"] = preview
            st.session_state.download_manifest = manifest_dict
        st.session_state.download_preview = preview
        st.info(preview.get("message", "Partial preview only"))

    preview = (manifest_dict or {}).get("preview") or st.session_state.get("download_preview")
    if preview:
        st.markdown("**Patch preview**")
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("Platform", preview.get("platform", "—"))
        pc2.metric("Confidence", f"{preview.get('confidence', 0):.0%}")
        pc3.metric("Files complete", f"{preview.get('n_complete', '—')}/{preview.get('n_total', '—')}")
        if preview.get("tissue_hint"):
            st.caption(preview["tissue_hint"])
        if preview.get("coord_scatter"):
            import plotly.express as px

            cs = preview["coord_scatter"]
            fig = px.scatter(x=cs["x"], y=cs["y"], labels={"x": "x", "y": "y"}, title="Coord preview patch")
            fig.update_yaxes(autorange="reversed")
            render_interactive_plot(fig, title="Download patch preview", module="study_setup", key="ss_dl_patch_scatter")

    if manifest_dict and manifest_dict.get("urls"):
        rows = []
        for u in manifest_dict["urls"]:
            total = u.get("bytes_total") or 0
            done = u.get("bytes_downloaded") or 0
            pct = f"{100 * done / total:.0f}%" if total else "—"
            rows.append(
                {
                    "filename": u.get("filename"),
                    "source": u.get("source"),
                    "role": u.get("role"),
                    "tech_hint": u.get("technology_hint"),
                    "status": u.get("status"),
                    "progress": pct,
                    "bytes": f"{done:,}" + (f" / {total:,}" if total else ""),
                    "warnings": u.get("error") or "",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        status = manifest_dict.get("status", "—")
        st.progress(
            sum(1 for u in manifest_dict["urls"] if u.get("status") == "complete") / max(len(manifest_dict["urls"]), 1),
            text=f"Job {manifest_dict.get('job_id', '—')}: {status}",
        )
        for w in manifest_dict.get("warnings") or []:
            st.warning(w)

    if st.button("Use Downloaded Dataset", key="ss_dl_ingest", disabled=not st.session_state.get("download_dir")):
        result = load_dataset_from_manifest(st.session_state.download_dir, manifest_dict)
        _store_ingestion(result)
        st.session_state.dataset_platform = result.get("platform")
        st.session_state.dataset_readiness = result.get("readiness")
        st.session_state.dataset_compatibility = result.get("compatibility")
        if result.get("adata") is not None:
            st.success(f"Ingested {result['platform']}: {result['adata'].n_obs} observations")
            from app.components.notification_center import push_notification

            push_notification(
                f"Ingested {result['adata'].n_obs:,} observations from downloaded bundle.",
                title="Download ingest complete",
                level="success",
                source="study_data",
            )
        else:
            st.warning(
                "Files inspected and readiness updated; full AnnData load may require a complete platform bundle."
            )


def _render_file_upload() -> None:
    st.markdown("#### Per-sample data upload")
    st.caption(
        "Upload one dataset per sample (Visium ZIP, Xenium ZIP, h5ad, or CSV matrix with coordinates). "
        "Cards sync with the sample metadata table above."
    )
    _render_per_sample_upload_cards()

    st.divider()
    st.markdown("#### Optional multimodal assets")
    tab_meta, tab_atac, tab_protein, tab_mut, tab_gt = st.tabs(
        ["Sample / clinical metadata", "ATAC", "Protein / CODEX", "Mutation / CNV", "Ground truth"]
    )
    with tab_meta:
        _upload_csv_metadata("Sample metadata CSV", "ps_sample_meta_csv", "sample_metadata_csv")
        _upload_csv_metadata("Clinical metadata CSV", "ps_clinical_meta_csv", "clinical_metadata")
    with tab_atac:
        _upload_unprocessed("ATAC peak matrix or fragments", "ps_atac_upload", "atac_data", ["csv", "h5ad", "tsv"])
    with tab_protein:
        _upload_unprocessed("Protein / CODEX matrix", "ps_protein_upload", "protein_data", ["csv", "h5ad"])
    with tab_mut:
        _upload_unprocessed("Mutation / CNV table", "ps_mutation_upload", "mutation_data", ["csv", "tsv"])
    with tab_gt:
        gt = st.file_uploader("Ground-truth reference (h5ad)", type=["h5ad"], key="ps_ground_truth")
        if gt is not None:
            try:
                from mbsi.io.generic import ingest_h5ad
                from mbsi.io.ingest import save_upload_to_temp

                path = save_upload_to_temp(gt, ".h5ad")
                adata_gt, _ = ingest_h5ad(path)
                st.session_state.ground_truth = adata_gt
                st.success(f"Ground truth loaded: {adata_gt.n_obs} cells")
            except Exception as exc:
                st.error(f"Ground truth load failed: {exc}")

    adata = st.session_state.get("adata")
    ingestion = st.session_state.get("ingestion_result", {})
    if ingestion.get("detection"):
        _render_detection_panel(ingestion["detection"])

    if adata is not None and "spatial" in adata.obsm:
        platform = st.session_state.get("mbsi_platform") or ingestion.get("platform")
        if platform == "stereo_seq":
            st.markdown("**Stereo-seq spatial preview**")
            from app.components.stereo_viewer import render_stereo_viewer

            fig = render_stereo_viewer(adata, module="study_setup", key_prefix="ps_stereo")
            if fig is not None:
                render_interactive_plot(fig, title="Stereo-seq viewer", module="study_setup", key="ps_stereo_preview")
        else:
            st.markdown("**Spatial preview**")
            color_by = "total_counts" if "total_counts" in adata.obs.columns else None
            if "cell_type" in adata.obs.columns:
                color_by = "cell_type"
            elif "cluster" in adata.obs.columns:
                color_by = "cluster"
            if color_by:
                fig = plot_qc_spatial(adata, color_by)
            else:
                import plotly.express as px

                coords = adata.obsm["spatial"]
                fig = px.scatter(x=coords[:, 0], y=coords[:, 1], labels={"x": "x", "y": "y"})
                fig.update_yaxes(autorange="reversed")
            render_interactive_plot(fig, title="Project spatial map", module="study_setup", key="ps_spatial_preview")
        score, _ = data_readiness_score(adata)
        safe_register_finding(
            f"Project data loaded: {adata.n_obs} spots, readiness {score}/100",
            section="study_setup",
            module="study_setup",
            title="Data loaded",
        )

    st.divider()
    if st.button("Load Demo Dataset (labeled demo)", key="ps_load_demo"):
        load_advanced_demo_into_session(force=True)
        st.session_state.using_synthetic_demo = True
        st.session_state.mbsi_platform = "demo"
        st.session_state.mbsi_readiness = {"status": "Synthetic demo data"}
        from app.components.notification_center import push_notification

        push_notification(
            "Sample demo dataset loaded for exploration.",
            title="Sample dataset loaded",
            level="info",
            source="study_data",
        )
        st.rerun()


def _uploaded_file_summary() -> List[str]:
    files: List[str] = []
    for sid, upload in (st.session_state.get("sample_uploads") or {}).items():
        if upload.get("uploaded_file_name"):
            files.append(f"{sid}: {upload['uploaded_file_name']} ({upload.get('status', 'unknown')})")
    if st.session_state.get("adata") is not None and not files:
        files.append("AnnData (spatial counts)")
    if st.session_state.get("uploaded_image") is not None:
        files.append("Histology image")
    if st.session_state.get("uploaded_segmentation") is not None:
        files.append("Segmentation mask")
    if st.session_state.get("clinical_metadata") is not None:
        files.append("Clinical metadata CSV")
    if st.session_state.get("atac_data") is not None:
        files.append("ATAC data")
    if st.session_state.get("protein_data") is not None:
        files.append("Protein / CODEX data")
    if st.session_state.get("mutation_data") is not None:
        files.append("Mutation / CNV data")
    if st.session_state.get("ground_truth") is not None:
        files.append("Ground-truth reference")
    if st.session_state.get("download_dir"):
        files.append(f"Downloaded dataset ({st.session_state.download_dir})")
    return files


def _compute_project_completeness() -> Tuple[int, List[str]]:
    meta = st.session_state.get("project_metadata", {})
    design = st.session_state.get("experimental_design", {})
    plat = st.session_state.get("platform_metadata", {})
    samples = st.session_state.get("sample_metadata")
    missing: List[str] = []
    score = 0

    checks = [
        (bool(meta.get("project_title", "").strip()), 12, "project title"),
        (bool(meta.get("biological_question", "").strip()), 12, "biological question"),
        (bool(meta.get("study_objective", "").strip()), 10, "study objective"),
        (bool(meta.get("disease_context", "").strip()) or bool(meta.get("therapeutic_context", "").strip()), 8, "disease or therapeutic context"),
        (bool(design.get("study_type")), 10, "study type"),
        (int(design.get("num_samples", 0)) >= 1, 8, "sample count"),
        (bool(design.get("primary_comparison", "").strip()), 5, "primary comparison"),
        (bool(design.get("comparison_groups", "").strip()), 5, "comparison groups"),
        (bool(plat.get("platforms")), 12, "platform selection"),
        (bool(plat.get("modalities")), 8, "modality selection"),
    ]
    for ok, pts, label in checks:
        if ok:
            score += pts
        else:
            missing.append(label)

    if isinstance(samples, pd.DataFrame) and not samples.empty and samples["sample_id"].notna().all():
        score += 10
    else:
        missing.append("sample metadata table")

    if design.get("has_replicates") in ("Yes", "No"):
        score += 10
    else:
        missing.append("replicate decision")

    return min(score, 100), missing


def _compute_dataset_readiness() -> Tuple[int, List[str]]:
    _ensure_primary_adata_from_uploads()
    adata = st.session_state.get("adata")
    missing: List[str] = []
    uploads = st.session_state.get("sample_uploads") or {}
    ingested = [u for u in uploads.values() if u.get("status") == "ingested"]

    if adata is None and not ingested:
        return 0, ["spatial omics file (h5ad, Visium ZIP, Xenium ZIP, or CSV + coordinates)"]

    if adata is None and ingested:
        return 25, ["primary AnnData load pending — click Start Analysis after ingest"]

    score, _ = data_readiness_score(adata)
    if "spatial" not in adata.obsm:
        missing.append("spatial coordinates in AnnData")
    if adata.n_vars < 20:
        missing.append("sufficient gene features")
    if adata.n_obs < 5:
        missing.append("minimum spot count")

    bonus = 0
    if st.session_state.get("uploaded_image") is not None:
        bonus += 5
    if st.session_state.get("clinical_metadata") is not None:
        bonus += 5
    if st.session_state.get("ground_truth") is not None:
        bonus += 10

    return min(int(score * 0.75 + bonus), 100), missing


def _build_compatibility_table() -> pd.DataFrame:
    adata = st.session_state.get("adata")
    ingestion = st.session_state.get("ingestion_result", {})
    detection = ingestion.get("detection")
    tech_key = st.session_state.get("selected_technology", "")
    io_matrix = get_compatibility_matrix(adata, detection)
    meta = st.session_state.get("project_metadata", {})
    design = st.session_state.get("experimental_design", {})
    plat = st.session_state.get("platform_metadata", {})
    project_missing = []
    if not meta.get("project_title"):
        project_missing.append("project title")
    if not design.get("comparison_groups"):
        project_missing.append("comparison groups")
    if not plat.get("platforms"):
        project_missing.append("platform metadata")

    rows = []
    for label, key in ANALYSIS_ROWS:
        if key == WorkflowModule.AI_REVIEW.value:
            status = "available"
            reason = "Available after pipeline findings are generated"
            req = [] if st.session_state.get("findings") or st.session_state.get("discovery_results") else ["discovery run findings"]
        elif key == WorkflowModule.REPORT_EXPORT.value:
            entry = io_matrix.get(key, {"status": "available", "reason": ""})
            status = entry.get("status", "available")
            reason = entry.get("reason", "Export always available")
            req = project_missing[:2] if project_missing else []
        else:
            entry = io_matrix.get(key, {"status": "unavailable", "reason": "not evaluated"})
            status = entry.get("status", "unavailable")
            reason = entry.get("reason", "")
            req = list(entry.get("required_missing", []))
            if adata is None:
                req.append("upload spatial omics data")
            req.extend(project_missing[:1])
            if key == WorkflowModule.BENCHMARK.value and st.session_state.get("ground_truth") is None:
                req.append("ground-truth reference")

        rows.append(
            {
                "Analysis": label,
                "Available": status,
                "Reason": reason,
                "Required missing items": ", ".join(dict.fromkeys(req)) if req else "—",
                "Recommended next step": recommended_next_step_for_module(key, status, req, adata is not None),
            }
        )
    return pd.DataFrame(rows)


def _available_analyses(compatibility_df: pd.DataFrame) -> List[str]:
    return compatibility_df.loc[compatibility_df["Available"].isin(["available", "warn"]), "Analysis"].tolist()


def _recommended_next_step(
    project_score: int,
    dataset_score: int,
    project_missing: List[str],
    dataset_missing: List[str],
) -> str:
    if project_score < 50:
        return f"Complete project metadata ({', '.join(project_missing[:3])})"
    if dataset_score == 0:
        return "Upload spatial omics files (h5ad, Visium ZIP, or CSV matrix + coordinates)"
    if dataset_score < 60:
        return "Continue to Data QC & Preprocessing to validate and improve data quality"
    if project_missing:
        return f"Refine study design: {', '.join(project_missing[:2])}"
    return "Continue to Data QC & Preprocessing"


def _render_readiness_section(
    project_score: int,
    dataset_score: int,
    project_missing: List[str],
    compatibility_df: pd.DataFrame,
) -> str:
    st.markdown("#### Readiness & compatibility")
    c1, c2 = st.columns(2)
    c1.metric("Project completeness", f"{project_score}/100")
    c2.metric("Dataset readiness", f"{dataset_score}/100")
    st.dataframe(compatibility_df, use_container_width=True, hide_index=True)
    st.session_state.project_completeness = project_score
    st.session_state.dataset_readiness = dataset_score
    st.session_state.dataset_compatibility = compatibility_df.to_dict("records")
    return _recommended_next_step(project_score, dataset_score, project_missing, [])


def _render_summary_card(
    recommended: str,
    compatibility_df: pd.DataFrame,
    uploaded_files: List[str],
) -> None:
    st.markdown("#### Project summary")
    meta = st.session_state.get("project_metadata", {})
    design = st.session_state.get("experimental_design", {})
    plat = st.session_state.get("platform_metadata", {})
    samples = st.session_state.get("sample_metadata")
    n_samples = len(samples) if isinstance(samples, pd.DataFrame) else int(design.get("num_samples", 0))
    available = _available_analyses(compatibility_df)

    st.markdown(
        f"""
        **Study:** {meta.get('project_title') or 'Untitled project'}  
        **Type:** {design.get('study_type', '—')} · **Samples:** {n_samples} · **Replicates:** {design.get('has_replicates', '—')} ({design.get('replicate_type', '—')})  
        **Groups:** {design.get('comparison_groups') or '—'}  
        **Platforms:** {', '.join(plat.get('platforms') or []) or '—'}  
        **Uploaded files:** {', '.join(uploaded_files) or 'None yet'}  
        **Available analyses:** {', '.join(available) or 'None until data is loaded'}  
        **Recommended next step:** {recommended}
        """
    )
