"""Final HTML/PDF report and data bundle generation."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mbsi.reports.biomarker_report import BIOMARKER_DISCLAIMER, generate_biomarker_report_text
from mbsi.reports.registry import get_notebook_entries, get_registered_outputs


def _session_snapshot() -> Dict[str, Any]:
    import streamlit as st

    analysis = st.session_state.get("analysis_results")
    return {
        "benchmark_results": st.session_state.get("benchmark_results"),
        "communication_results": st.session_state.get("communication_results"),
        "tme_results": st.session_state.get("tme_results"),
        "discovery_results": st.session_state.get("discovery_results"),
        "analysis_results": analysis,
        "marker_table": st.session_state.get("marker_table"),
        "spatial_stats": st.session_state.get("spatial_stats"),
        "using_synthetic_demo": st.session_state.get("using_synthetic_demo", True),
        "last_run": st.session_state.get("last_run"),
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


def generate_final_html_report(output_dir: Path, snapshot: Optional[Dict[str, Any]] = None) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snap = snapshot or _session_snapshot()
    reg = snap.get("registered") or get_registered_outputs()
    notebook = snap.get("notebook") or get_notebook_entries()
    narrative = generate_biomarker_report_text(
        benchmark_results=snap.get("benchmark_results"),
        communication_results=snap.get("communication_results"),
        tme_results=snap.get("tme_results"),
    )
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"mbsi_final_report_{ts}.html"
    fig_rows = "".join(
        f"<li>{f.get('module')}: {f.get('title')} ({f.get('timestamp', '')[:19]})</li>"
        for f in reg.get("figures", [])
    )
    tbl_rows = "".join(
        f"<li>{t.get('module')}: {t.get('title')} ({t.get('rows', 0)} rows)</li>"
        for t in reg.get("tables", [])
    )
    finding_rows = "".join(
        f"<li>{f.get('module')}: {f.get('title')} — {f.get('text', '')}</li>"
        for f in reg.get("findings", [])
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
pre {{ white-space: pre-wrap; background: #0d1828; padding: 1rem; border-radius: 8px; }}
.notebook {{ background: #0d1828; padding: 1rem; border-radius: 8px; }}
</style></head><body>
<h1>MBSI Studio — Final Report</h1>
<div class="disclaimer">{BIOMARKER_DISCLAIMER}</div>
{analysis_block}
<h2>Results Notebook ({len(notebook)} entries)</h2>
<div class="notebook">{_notebook_html(notebook)}</div>
<h2>Registered Figures</h2><ul>{fig_rows or '<li>None</li>'}</ul>
<h2>Registered Tables</h2><ul>{tbl_rows or '<li>None</li>'}</ul>
<h2>Findings</h2><ul>{finding_rows or '<li>None</li>'}</ul>
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
