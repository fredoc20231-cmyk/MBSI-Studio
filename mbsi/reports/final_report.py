"""Final HTML/PDF report and data bundle generation."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mbsi.reports.biomarker_report import BIOMARKER_DISCLAIMER, generate_biomarker_report_text
from mbsi.reports.registry import get_notebook_entries, get_registered_outputs
from mbsi.schema.report import ReportMetadata


def _session_snapshot() -> Dict[str, Any]:
    import streamlit as st

    analysis = st.session_state.get("analysis_results")
    sample_meta = st.session_state.get("sample_metadata")
    if hasattr(sample_meta, "to_dict"):
        sample_meta = sample_meta.to_dict("records")
    return {
        "project_metadata": st.session_state.get("project_metadata"),
        "experimental_design": st.session_state.get("experimental_design"),
        "platform_metadata": st.session_state.get("platform_metadata"),
        "sample_metadata": sample_meta,
        "project_completeness": st.session_state.get("project_completeness"),
        "dataset_readiness": st.session_state.get("dataset_readiness"),
        "mbsi_platform": st.session_state.get("mbsi_platform"),
        "stereo_seq_readiness": st.session_state.get("stereo_seq_readiness"),
        "stereo_seq_profile": st.session_state.get("stereo_seq_profile"),
        "uploaded_files_summary": _uploaded_files_from_session(),
        "benchmark_results": st.session_state.get("benchmark_results"),
        "communication_results": st.session_state.get("communication_results"),
        "tme_results": st.session_state.get("tme_results"),
        "discovery_results": st.session_state.get("discovery_results"),
        "findings": st.session_state.get("findings"),
        "evidence": st.session_state.get("evidence"),
        "validation_recommendations": st.session_state.get("discovery_results", {}).get("validation_recommendations"),
        "analysis_results": analysis,
        "marker_table": st.session_state.get("marker_table"),
        "spatial_stats": st.session_state.get("spatial_stats"),
        "segmentation_qc": st.session_state.get("segmentation_qc"),
        "tissue_mask_present": st.session_state.get("tissue_mask") is not None,
        "cell_mask_present": st.session_state.get("cell_mask") is not None,
        "compartment_labels_present": st.session_state.get("compartment_labels") is not None,
        "boundary_map_present": st.session_state.get("boundary_map") is not None,
        "qc_settings": st.session_state.get("qc_settings"),
        "preprocess_settings": (st.session_state.get("run_outputs") or {}).get("qc_preprocess"),
        "segmentation_method": st.session_state.get("seg_tissue_method"),
        "selected_technology": st.session_state.get("selected_technology"),
        "technology_spec": (st.session_state.get("mbsi_readiness") or {}).get("technology_spec"),
        "using_synthetic_demo": st.session_state.get("using_synthetic_demo", False),
        "last_run": st.session_state.get("last_run"),
        "download_manifest": st.session_state.get("download_manifest"),
        "download_dir": st.session_state.get("download_dir"),
        "dataset_platform": st.session_state.get("dataset_platform"),
        "download_preview": st.session_state.get("download_preview"),
        "registered": get_registered_outputs(),
        "notebook": get_notebook_entries(),
    }


def _notebook_html(entries: List[Dict[str, Any]]) -> str:
    if not entries:
        return "<p>No notebook entries.</p>"
    rows = []
    for e in entries:
        etype = e.get("type", "item")
        title = e.get("title") or e.get("text", "Untitled")
        module = e.get("module", "—")
        ts = e.get("timestamp", "")[:19].replace("T", " ")
        detail = ""
        if etype == "finding":
            detail = f"<br><em>{e.get('text', '')}</em>"
        elif etype == "table":
            detail = f"<br><em>{e.get('rows', 0)} rows · {', '.join(e.get('columns', [])[:5])}</em>"
        rows.append(f"<li><strong>[{etype}] {title}</strong> ({module}, {ts}){detail}</li>")
    return "<ul>" + "\n".join(rows) + "</ul>"


def _findings_html(findings: List[Dict[str, Any]]) -> str:
    if not findings:
        return "<p>No structured findings.</p>"
    rows = []
    for f in sorted(findings, key=lambda x: x.get("confidence_score", 0), reverse=True):
        badge = f.get("confidence_level", "Hypothesis")
        rows.append(
            f"<li><strong>{f.get('title')}</strong> "
            f"<span class='badge'>{badge} ({f.get('confidence_score', 0):.0f})</span><br>"
            f"<em>{f.get('summary', '')}</em><br>"
            f"Type: {f.get('finding_type')} · Module: {f.get('module')}</li>"
        )
    return "<ul>" + "\n".join(rows) + "</ul>"


def _evidence_html(evidence: List[Dict[str, Any]]) -> str:
    if not evidence:
        return "<p>No evidence linked.</p>"
    rows = [f"<li>{e.get('title')} ({e.get('evidence_type')}, {e.get('source_module')})</li>" for e in evidence[:20]]
    return "<ul>" + "\n".join(rows) + "</ul>"


def _validation_html(validations: List[Dict[str, Any]]) -> str:
    if not validations:
        return "<p>No validation recommendations.</p>"
    rows = []
    for v in validations:
        recs = v.get("recommendations", [])
        rec_str = "<ul>" + "".join(f"<li>{r}</li>" for r in recs) + "</ul>"
        rows.append(f"<li><strong>{v.get('title')}</strong> ({v.get('confidence_level')}){rec_str}</li>")
    return "<ul>" + "\n".join(rows) + "</ul>"


def _confidence_summary(findings: List[Dict[str, Any]]) -> str:
    if not findings:
        return "No findings scored."
    levels = {}
    for f in findings:
        lvl = f.get("confidence_level", "Hypothesis")
        levels[lvl] = levels.get(lvl, 0) + 1
    return ", ".join(f"{k}: {v}" for k, v in sorted(levels.items()))


def _uploaded_files_from_session() -> List[str]:
    import streamlit as st

    files: List[str] = []
    if st.session_state.get("adata") is not None:
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
    return files


def _download_section_html(snap: Dict[str, Any]) -> str:
    manifest = snap.get("download_manifest")
    if not manifest and not snap.get("download_dir"):
        return ""

    job_id = manifest.get("job_id", "—") if manifest else "—"
    status = manifest.get("status", "—") if manifest else "—"
    platform = manifest.get("detected_platform") or snap.get("dataset_platform") or "—"
    readiness = manifest.get("readiness") if manifest else {}
    preview = (manifest or {}).get("preview") or snap.get("download_preview") or {}
    dl_dir = snap.get("download_dir") or manifest.get("output_dir", "—")

    rows = []
    for u in (manifest or {}).get("urls") or []:
        rows.append(
            f"<li><strong>{u.get('filename')}</strong> — {u.get('status')} · "
            f"{u.get('source')} · {u.get('role')} · "
            f"sha256: {(u.get('sha256') or '—')[:16]}… · "
            f"<a href=\"{u.get('url', '')}\">{u.get('url', '')[:60]}</a></li>"
        )
    files_html = "<ul>" + "\n".join(rows) + "</ul>" if rows else "<p>No download manifest entries.</p>"

    return f"""
<h2>Downloaded Dataset</h2>
<ul>
<li><strong>Job ID:</strong> {job_id}</li>
<li><strong>Status:</strong> {status}</li>
<li><strong>Output directory:</strong> {dl_dir}</li>
<li><strong>Created:</strong> {manifest.get('created_at', '—') if manifest else '—'}</li>
<li><strong>Detected platform:</strong> {platform}</li>
<li><strong>Readiness score:</strong> {readiness.get('score', snap.get('dataset_readiness', '—'))}</li>
<li><strong>Readiness status:</strong> {readiness.get('status', '—')}</li>
</ul>
<h3>Source URLs &amp; Files</h3>
{files_html}
<h3>Patch Preview Summary</h3>
<p>{preview.get('message', 'No patch preview run.')}</p>
<ul>
<li>Preview platform: {preview.get('platform', '—')}</li>
<li>Confidence: {preview.get('confidence', '—')}</li>
<li>Files complete: {preview.get('n_complete', '—')} / {preview.get('n_total', '—')}</li>
<li>Tissue hint: {preview.get('tissue_hint') or '—'}</li>
</ul>
<p><em>Partial preview only when dataset incomplete — full analysis requires complete dataset.</em></p>"""


def _sample_table_html(samples: Any) -> str:
    if not samples:
        return "<p>No sample metadata captured.</p>"
    if not isinstance(samples, list):
        return "<p>Sample metadata not in list form.</p>"
    headers = ["sample_id", "patient_id", "condition", "timepoint", "replicate_id", "technology", "platform"]
    head = "".join(f"<th>{h}</th>" for h in headers)
    rows = []
    for s in samples:
        if not isinstance(s, dict):
            continue
        cells = "".join(f"<td>{s.get(h, '—')}</td>" for h in headers)
        rows.append(f"<tr>{cells}</tr>")
    if not rows:
        return "<p>No sample rows.</p>"
    return f"<table border='1' cellpadding='4'><tr>{head}</tr>{''.join(rows)}</table>"


def _technology_profile_html(snap: Dict[str, Any]) -> str:
    spec = snap.get("technology_spec") or {}
    tech_key = snap.get("selected_technology") or snap.get("mbsi_platform") or spec.get("key", "—")
    if not spec and not tech_key:
        return "<p>No technology profile selected.</p>"
    req = spec.get("required_files") or []
    req_html = "<ul>" + "".join(f"<li>{r}</li>" for r in req) + "</ul>" if req else "<p>—</p>"
    return f"""
<h2>Technology Profile</h2>
<ul>
<li><strong>Technology:</strong> {spec.get('label', tech_key)}</li>
<li><strong>Normalization:</strong> {spec.get('normalization_strategy', '—')}</li>
<li><strong>Segmentation logic:</strong> {spec.get('segmentation_logic', '—')}</li>
</ul>
<h3>Required files</h3>
{req_html}
"""


def _qc_and_stats_html(snap: Dict[str, Any]) -> str:
    qc = snap.get("qc_settings") or {}
    pre = (snap.get("preprocess_settings") or {}).get("preprocess", {}).get("outputs", {})
    if not qc and not pre:
        return "<p>No QC or statistical settings recorded — run QC & Preprocessing.</p>"
    return f"""
<h2>QC Criteria &amp; Statistical Settings</h2>
<ul>
<li>Min counts: {qc.get('min_counts', '—')}</li>
<li>Max mito %: {qc.get('max_mito_pct', '—')}</li>
<li>FDR threshold: {qc.get('fdr', '—')}</li>
<li>P-value threshold: {qc.get('pval', '—')}</li>
<li>Log2FC threshold: {qc.get('log2fc', '—')}</li>
<li>Clustering method: {qc.get('clustering_method') or pre.get('clustering_method', '—')}</li>
<li>Clustering backend: {pre.get('clustering_fallback') or pre.get('clustering_method', '—')}</li>
<li>Reference marker panel: {qc.get('marker_panel') or pre.get('marker_panel', '—')}</li>
<li>Normalization: {pre.get('normalization_strategy', '—')}</li>
</ul>
"""


def _methods_html(snap: Dict[str, Any]) -> str:
    seg_method = snap.get("segmentation_method") or "—"
    qc = snap.get("qc_settings") or {}
    demo_note = " (demo data)" if snap.get("using_synthetic_demo") else ""
    return f"""
<h2>Analysis Methods</h2>
<ul>
<li>Data source{demo_note}: {'synthetic demo' if snap.get('using_synthetic_demo') else 'uploaded spatial omics'}</li>
<li>QC thresholds: min counts {qc.get('min_counts', '—')}, max mito {qc.get('max_mito_pct', '—')}%</li>
<li>Clustering: {qc.get('clustering_method', 'Leiden')}</li>
<li>Segmentation method: {seg_method}</li>
<li>Discovery pipeline: benchmark hub, communication intelligence, TME analysis, confidence scoring</li>
<li>Spatial analysis: PCA, kNN graph, marker ranking, Moran's I / Geary's C</li>
</ul>
"""


def _limitations_html(snap: Dict[str, Any]) -> str:
    limits = []
    if snap.get("using_synthetic_demo"):
        limits.append("Analysis used synthetic demo data — not suitable for clinical decisions.")
    if (snap.get("dataset_readiness") or 0) < 60:
        limits.append("Dataset readiness below recommended threshold — partial analyses may apply.")
    pre = (snap.get("preprocess_settings") or {}).get("preprocess", {}).get("outputs", {})
    fb = pre.get("clustering_fallback", "")
    if fb and "unavailable" in str(fb).lower():
        limits.append(f"Clustering fallback: {fb}")
    manifest = snap.get("download_manifest") or {}
    for w in manifest.get("warnings") or []:
        limits.append(str(w))
    if not limits:
        limits.append("Standard computational-hypothesis limitations apply — validate findings experimentally.")
    return "<ul>" + "".join(f"<li>{l}</li>" for l in limits) + "</ul>"


def _reproducibility_manifest_html(snap: Dict[str, Any]) -> str:
    discovery = snap.get("discovery_results") or {}
    run_outputs = snap.get("run_outputs") or {}
    notebook = snap.get("notebook") or []
    files = snap.get("uploaded_files_summary") or []
    return f"""
<h2>Reproducibility Manifest</h2>
<ul>
<li>Discovery run ID: {discovery.get('run_id', 'N/A')}</li>
<li>Last pipeline run: {snap.get('last_run', 'N/A')}</li>
<li>Workflow runs logged: {len(run_outputs)} modules</li>
<li>Notebook entries: {len(notebook)}</li>
<li>Files ingested: {', '.join(files) or '—'}</li>
<li>Dataset readiness: {snap.get('dataset_readiness', '—')}/100</li>
<li>Project completeness: {snap.get('project_completeness', '—')}/100</li>
<li>Technology: {snap.get('selected_technology') or snap.get('mbsi_platform', '—')}</li>
</ul>
"""


def _project_setup_html(snap: Dict[str, Any]) -> str:
    meta = snap.get("project_metadata") or {}
    design = snap.get("experimental_design") or {}
    plat = snap.get("platform_metadata") or {}
    samples = snap.get("sample_metadata") or []
    n_samples = len(samples) if isinstance(samples, list) else "—"
    files = snap.get("uploaded_files_summary") or []
    if not meta and not design:
        return "<p>No project setup metadata captured.</p>"
    return f"""
<h2>Project Setup</h2>
<ul>
<li><strong>Title:</strong> {meta.get('project_title') or '—'}</li>
<li><strong>Biological question:</strong> {meta.get('biological_question') or '—'}</li>
<li><strong>Study objective:</strong> {meta.get('study_objective') or '—'}</li>
<li><strong>Organism:</strong> {meta.get('organism') or '—'}</li>
<li><strong>Disease context:</strong> {meta.get('disease_context') or '—'}</li>
<li><strong>Therapeutic context:</strong> {meta.get('therapeutic_context') or '—'}</li>
<li><strong>Study type:</strong> {design.get('study_type') or '—'}</li>
<li><strong>Primary comparison:</strong> {design.get('primary_comparison') or '—'}</li>
<li><strong>Secondary comparisons:</strong> {design.get('secondary_comparisons') or '—'}</li>
<li><strong>Timepoints:</strong> {design.get('timepoints') or '—'}</li>
<li><strong>Treatment arms:</strong> {design.get('treatment_arms') or '—'}</li>
<li><strong>Samples:</strong> {n_samples}</li>
<li><strong>Replicates:</strong> {design.get('has_replicates', '—')} ({design.get('replicate_type', '—')})</li>
<li><strong>Comparison groups:</strong> {design.get('comparison_groups') or '—'}</li>
<li><strong>Platforms:</strong> {', '.join(plat.get('platforms') or []) or '—'}</li>
<li><strong>Modalities:</strong> {', '.join(plat.get('modalities') or []) or '—'}</li>
<li><strong>Files used:</strong> {', '.join(files) or '—'}</li>
<li><strong>Project completeness:</strong> {snap.get('project_completeness', '—')}/100</li>
<li><strong>Dataset readiness:</strong> {snap.get('dataset_readiness', '—')}/100</li>
</ul>
<h3>Sample table</h3>
{_sample_table_html(samples)}
"""


def _stereo_seq_report_html(snap: Dict[str, Any]) -> str:
    plat = snap.get("platform_metadata") or {}
    platforms = plat.get("platforms") or []
    mbsi_platform = snap.get("mbsi_platform") or ""
    if mbsi_platform != "stereo_seq" and not any("Stereo-seq" in p for p in platforms):
        return ""

    stereo_ready = snap.get("stereo_seq_readiness") or {}
    profile = snap.get("stereo_seq_profile") or {}
    adata_summary = ""
    analysis = snap.get("analysis_results") or {}
    adata = analysis.get("adata")
    if adata is not None:
        n_bins = int((adata.obs.get("stereo_scale", "bin") == "bin").sum()) if "stereo_scale" in adata.obs else adata.n_obs
        n_cells = int(adata.obs["cell_id"].notna().sum()) if "cell_id" in adata.obs else "—"
        n_regions = adata.obs["region_id"].nunique() if "region_id" in adata.obs else "—"
        adata_summary = f"""
<ul>
<li>Bins / observations: {adata.n_obs:,}</li>
<li>Genes: {adata.n_vars:,}</li>
<li>Cell-level obs: {n_cells}</li>
<li>Regions: {n_regions}</li>
<li>Readiness score: {stereo_ready.get('score', snap.get('dataset_readiness', '—'))}</li>
<li>Analysis scale: {profile.get('active_scale', 'bin')}</li>
</ul>"""

    discovery = snap.get("discovery_results") or {}
    stereo_findings = [f for f in (snap.get("findings") or []) if f.get("platform") == "stereo_seq"]
    findings_block = _findings_html(stereo_findings) if stereo_findings else "<p>No Stereo-seq-specific discovery findings yet.</p>"

    return f"""
<h2>STOmics Stereo-seq</h2>
<h3>Platform Summary</h3>
<p>Ultra-high-resolution spatial transcriptomics with multi-scale bin/cell/region analysis.</p>
<h3>Resolution Profile</h3>
<p>Resolution class: ultra_high · Default scale: {profile.get('active_scale', 'bin')}</p>
<h3>Bin / Cell Statistics</h3>
{adata_summary or '<p>Upload Stereo-seq data to populate statistics.</p>'}
<h3>Discovery Findings</h3>
{findings_block}
<h3>Confidence &amp; Validation</h3>
<p>{_confidence_summary(stereo_findings or snap.get('findings') or [])}</p>
<p>Validation: {_validation_html(snap.get('validation_recommendations') or discovery.get('validation_recommendations') or [])}</p>
"""


def _segmentation_report_html(snap: Dict[str, Any]) -> str:
    qc = snap.get("segmentation_qc") or {}
    metrics = qc.get("metrics", {}) if isinstance(qc, dict) else {}
    warnings = qc.get("warnings", []) if isinstance(qc, dict) else []
    if not qc and not snap.get("tissue_mask_present"):
        return ""
    warn_html = "<ul>" + "".join(f"<li>{w}</li>" for w in warnings) + "</ul>" if warnings else "<p>No warnings.</p>"
    return f"""
<h2>Segmentation &amp; Registration</h2>
<ul>
<li>Tissue mask: {'yes' if snap.get('tissue_mask_present') else 'no'}</li>
<li>Cell mask: {'yes' if snap.get('cell_mask_present') else 'no'}</li>
<li>Compartments: {'yes' if snap.get('compartment_labels_present') else 'no'}</li>
<li>Boundary map: {'yes' if snap.get('boundary_map_present') else 'no'}</li>
<li>QC pass: {qc.get('qc_pass', '—')}</li>
<li>Confidence: {metrics.get('segmentation_confidence', '—')}</li>
<li>Tissue coverage: {metrics.get('percent_tissue_covered', '—')}%</li>
<li>Spots in tissue: {metrics.get('percent_spots_inside_tissue', '—')}%</li>
</ul>
<h3>Warnings</h3>
{warn_html}
<p><em>Downstream: spatial analysis filtering, TME boundaries, discovery findings.</em></p>"""


def generate_final_html_report(output_dir: Path, snapshot: Optional[Dict[str, Any]] = None) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snap = snapshot or _session_snapshot()
    report_meta = ReportMetadata.from_session_snapshot(snap)
    reg = snap.get("registered") or get_registered_outputs()
    notebook = snap.get("notebook") or get_notebook_entries()
    findings = snap.get("findings") or []
    evidence = snap.get("evidence") or []
    validations = snap.get("validation_recommendations") or []
    discovery = snap.get("discovery_results") or {}
    if not findings and discovery.get("findings"):
        findings = discovery["findings"]
    if not evidence and discovery.get("evidence"):
        evidence = discovery["evidence"]
    if not validations and discovery.get("validation_recommendations"):
        validations = discovery["validation_recommendations"]

    narrative = generate_biomarker_report_text(
        benchmark_results=snap.get("benchmark_results"),
        communication_results=snap.get("communication_results"),
        tme_results=snap.get("tme_results"),
    )
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"mbsi_final_report_{ts}.html"

    top_finding = findings[0]["title"] if findings else "No findings yet"
    exec_summary = (
        f"MBSI Discovery Operating System report — {len(findings)} findings, "
        f"confidence mix: {_confidence_summary(findings)}. "
        f"Top finding: {top_finding}."
    )

    fig_rows = "".join(
        f"<li>{f.get('module')}: {f.get('title')} ({f.get('timestamp', '')[:19]})</li>"
        for f in reg.get("figures", [])
    )
    tbl_rows = "".join(
        f"<li>{t.get('module')}: {t.get('title')} ({t.get('rows', 0)} rows)</li>"
        for t in reg.get("tables", [])
    )
    analysis = snap.get("analysis_results")
    analysis_block = ""
    if analysis:
        demo_label = " (demo data)" if snap.get("using_synthetic_demo") else " (uploaded data)"
        adata = analysis.get("adata")
        n_clusters = adata.obs["cluster"].nunique() if adata is not None and "cluster" in adata.obs else "—"
        qc = analysis.get("qc_summary")
        markers = snap.get("marker_table")
        stats = snap.get("spatial_stats")
        analysis_block = f"""
<h2>Spatial Analysis{demo_label}</h2>
<ul>
<li>Clusters: {n_clusters}</li>
<li>QC summary rows: {len(qc) if qc is not None else 0}</li>
<li>Marker rows: {len(markers) if markers is not None else 0}</li>
<li>Spatial stats genes: {len(stats) if stats is not None else 0}</li>
</ul>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>MBSI Final Report</title>
<style>
body {{ font-family: Inter, sans-serif; background: #07111f; color: #f4f7fb; padding: 2rem; }}
.disclaimer {{ background: #101d2e; border-left: 4px solid #ffb020; padding: 1rem; margin: 1rem 0; }}
.badge {{ background: #1a3a5c; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; }}
pre {{ white-space: pre-wrap; background: #0d1828; padding: 1rem; border-radius: 8px; }}
.notebook {{ background: #0d1828; padding: 1rem; border-radius: 8px; }}
</style></head><body>
<h1>MBSI Studio — Final Report</h1>
<div class="disclaimer">{BIOMARKER_DISCLAIMER}</div>
<h2>Executive Summary</h2><p>{exec_summary}</p>
{_project_setup_html(snap)}
{_technology_profile_html(snap)}
{_download_section_html(snap)}
{_qc_and_stats_html(snap)}
<h2>Top Findings</h2>{_findings_html(findings)}
<h2>Evidence Summary</h2>{_evidence_html(evidence)}
<h2>Confidence Summary</h2><p>{_confidence_summary(findings)}</p>
<h2>Pathways &amp; Biomarkers</h2>{_findings_html([f for f in findings if f.get('finding_type') in ('lr_pathway','pathway','biomarker','tme_program')])}
<h2>Validation Recommendations</h2>{_validation_html(validations)}
{_stereo_seq_report_html(snap)}
{_segmentation_report_html(snap)}
{analysis_block}
{_methods_html(snap)}
<h2>Limitations</h2>{_limitations_html(snap)}
{_reproducibility_manifest_html(snap)}
<h2>Traceability</h2>
<ul>
<li>Run ID: {discovery.get('run_id', 'N/A')}</li>
<li>Last run: {snap.get('last_run', 'N/A')}</li>
<li>Notebook entries: {len(notebook)}</li>
<li>Report traceability: {len(report_meta.finding_ids)} findings, {len(report_meta.evidence_ids)} evidence, {len(report_meta.samples)} samples</li>
<li>Project: {report_meta.project.title or '—'}</li>
</ul>
<h2>Results Notebook ({len(notebook)} entries)</h2>
<div class="notebook">{_notebook_html(notebook)}</div>
<h2>Registered Figures</h2><ul>{fig_rows or '<li>None</li>'}</ul>
<h2>Registered Tables</h2><ul>{tbl_rows or '<li>None</li>'}</ul>
<h2>Narrative</h2><pre>{narrative}</pre>
<p><em>Generated {ts} UTC</em></p>
</body></html>"""
    path.write_text(html, encoding="utf-8")
    return path


def generate_final_pdf_report(output_dir: Path, snapshot: Optional[Dict[str, Any]] = None) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snap = snapshot or _session_snapshot()
    narrative = generate_biomarker_report_text(
        benchmark_results=snap.get("benchmark_results"),
        communication_results=snap.get("communication_results"),
        tme_results=snap.get("tme_results"),
    )
    notebook = snap.get("notebook") or get_notebook_entries()
    nb_lines = [f"- [{e.get('type')}] {e.get('title', e.get('text', ''))} ({e.get('module')})" for e in notebook]
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"mbsi_final_report_{ts}.pdf.txt"
    body = f"{BIOMARKER_DISCLAIMER}\n\n## Notebook\n" + "\n".join(nb_lines) + f"\n\n{narrative}"
    path.write_text(body, encoding="utf-8")
    return path


def create_data_bundle(output_dir: Path, snapshot: Optional[Dict[str, Any]] = None) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snap = snapshot or _session_snapshot()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    bundle = output_dir / f"mbsi_data_bundle_{ts}.zip"
    manifest = {
        "generated": ts,
        "last_run": snap.get("last_run"),
        "registered": snap.get("registered") or get_registered_outputs(),
        "notebook": snap.get("notebook") or get_notebook_entries(),
        "disclaimer": BIOMARKER_DISCLAIMER,
    }
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))
        narrative = generate_biomarker_report_text(
            benchmark_results=snap.get("benchmark_results"),
            communication_results=snap.get("communication_results"),
            tme_results=snap.get("tme_results"),
        )
        zf.writestr("report.txt", narrative)
        zf.writestr("notebook.json", json.dumps(manifest["notebook"], indent=2, default=str))
    return bundle
