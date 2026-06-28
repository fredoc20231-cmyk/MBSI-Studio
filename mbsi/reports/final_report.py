"""Final HTML/PDF report and data bundle generation."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from mbsi.reports.biomarker_report import BIOMARKER_DISCLAIMER, generate_biomarker_report_text
from mbsi.reports.registry import get_registered_outputs


def _session_snapshot() -> Dict[str, Any]:
    """Build report payload from typical session keys (caller may pass via globals in UI)."""
    import streamlit as st

    return {
        "benchmark_results": st.session_state.get("benchmark_results"),
        "communication_results": st.session_state.get("communication_results"),
        "tme_results": st.session_state.get("tme_results"),
        "discovery_results": st.session_state.get("discovery_results"),
        "last_run": st.session_state.get("last_run"),
        "registered": get_registered_outputs(),
    }


def generate_final_html_report(output_dir: Path, snapshot: Optional[Dict[str, Any]] = None) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snap = snapshot or _session_snapshot()
    reg = snap.get("registered") or get_registered_outputs()
    narrative = generate_biomarker_report_text(
        benchmark_results=snap.get("benchmark_results"),
        communication_results=snap.get("communication_results"),
        tme_results=snap.get("tme_results"),
    )
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"mbsi_final_report_{ts}.html"
    fig_rows = "".join(
        f"<li>{f.get('module')}: {f.get('title')}</li>" for f in reg.get("figures", [])
    )
    tbl_rows = "".join(
        f"<li>{t.get('module')}: {t.get('title')} ({t.get('rows', 0)} rows)</li>"
        for t in reg.get("tables", [])
    )
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>MBSI Final Report</title>
<style>
body {{ font-family: Inter, sans-serif; background: #07111f; color: #f4f7fb; padding: 2rem; }}
.disclaimer {{ background: #101d2e; border-left: 4px solid #ffb020; padding: 1rem; margin: 1rem 0; }}
pre {{ white-space: pre-wrap; background: #0d1828; padding: 1rem; border-radius: 8px; }}
</style></head><body>
<h1>MBSI Studio — Final Report</h1>
<div class="disclaimer">{BIOMARKER_DISCLAIMER}</div>
<h2>Registered Figures</h2><ul>{fig_rows or '<li>None</li>'}</ul>
<h2>Registered Tables</h2><ul>{tbl_rows or '<li>None</li>'}</ul>
<h2>Narrative</h2><pre>{narrative}</pre>
<p><em>Generated {ts} UTC</em></p>
</body></html>"""
    path.write_text(html, encoding="utf-8")
    return path


def generate_final_pdf_report(output_dir: Path, snapshot: Optional[Dict[str, Any]] = None) -> Path:
    """Fallback: write plain-text report with .pdf extension if no PDF engine available."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snap = snapshot or _session_snapshot()
    narrative = generate_biomarker_report_text(
        benchmark_results=snap.get("benchmark_results"),
        communication_results=snap.get("communication_results"),
        tme_results=snap.get("tme_results"),
    )
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"mbsi_final_report_{ts}.pdf.txt"
    path.write_text(f"{BIOMARKER_DISCLAIMER}\n\n{narrative}", encoding="utf-8")
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
        "disclaimer": BIOMARKER_DISCLAIMER,
    }
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        narrative = generate_biomarker_report_text(
            benchmark_results=snap.get("benchmark_results"),
            communication_results=snap.get("communication_results"),
            tme_results=snap.get("tme_results"),
        )
        zf.writestr("report.txt", narrative)
    return bundle
