"""Export buttons and snapshot utilities."""

import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st

from app.components.page_utils import OUTPUT_DIR, save_metrics, save_reconstructed


def save_snapshot(name: Optional[str] = None) -> Path:
    """Save current session metrics and state snapshot."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / (name or f"snapshot_{stamp}.json")
    payload = {
        "project": st.session_state.get("project_name", "MBSI"),
        "metrics": st.session_state.get("metrics", {}),
        "analysis_state": st.session_state.get("analysis_state", {}),
        "last_run": st.session_state.get("last_run"),
        "n_cells": st.session_state.get("spatial_demo", {}).get("n_cells_total"),
    }
    path.write_text(json.dumps(payload, indent=2, default=str))
    return path


def render_export_buttons() -> None:
    """Full export control panel."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    st.markdown("#### Export Artifacts")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Export h5ad", type="primary", use_container_width=True, key="exp_h5ad"):
            if st.session_state.reconstructed is not None:
                p = save_reconstructed()
                st.success(f"Saved {p}")
            else:
                st.warning("No reconstruction available.")
    with c2:
        if st.button("Export metrics CSV", use_container_width=True, key="exp_csv"):
            _export_csv()
    with c3:
        if st.button("Export HTML report", use_container_width=True, key="exp_html"):
            _export_html()

    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("Export figures (PNG)", use_container_width=True, key="exp_png"):
            _export_figures_placeholder()
    with c5:
        if st.button("Export ZIP bundle", use_container_width=True, key="exp_zip"):
            path = _export_zip_bundle()
            st.success(f"Bundle: {path}")
    with c6:
        snap = save_snapshot()
        st.download_button(
            "Download snapshot JSON",
            snap.read_text(),
            file_name=snap.name,
            use_container_width=True,
        )


def _export_csv() -> None:
    import pandas as pd

    rows = []
    metrics = st.session_state.get("metrics") or {}
    for k, v in metrics.items():
        rows.append({"metric": k, "value": v})
    demo = st.session_state.get("spatial_demo") or {}
    if "lr_pathways" in demo and demo["lr_pathways"] is not None:
        demo["lr_pathways"].to_csv(OUTPUT_DIR / "lr_pathways.csv", index=False)
    pd.DataFrame(rows).to_csv(OUTPUT_DIR / "metrics.csv", index=False)
    save_metrics()
    st.success(f"Saved {OUTPUT_DIR / 'metrics.csv'}")


def _export_html() -> None:
    from mbsi.copilot.report_text import generate_results_text, generate_methods_text

    metrics = st.session_state.get("metrics") or {}
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>MBSI Studio Report</title>
<style>
body{{background:#07111f;color:#f4f7fb;font-family:system-ui,sans-serif;padding:32px;}}
.panel{{background:#0d1828;border:1px solid #22314a;border-radius:10px;padding:20px;margin:16px 0;}}
h1{{color:#4f7cff;}} h2{{color:#9aa7b8;font-size:1rem;text-transform:uppercase;}}
</style></head><body>
<h1>MBSI Studio — Spatial Biology Report</h1>
<div class="panel"><h2>Methods</h2><p>{generate_methods_text(st.session_state.get('preprocessing_params', {}))}</p></div>
<div class="panel"><h2>Results</h2><pre>{generate_results_text(metrics)}</pre></div>
</body></html>"""
    path = OUTPUT_DIR / "report.html"
    path.write_text(html, encoding="utf-8")
    st.success(f"Saved {path}")


def _export_figures_placeholder() -> None:
    """Save histology PNG if available."""
    demo = st.session_state.get("spatial_demo") or {}
    if "histology_pil" in demo:
        path = OUTPUT_DIR / "histology_export.png"
        demo["histology_pil"].save(path)
        st.success(f"Saved {path}")
    else:
        st.info("Histology figure saved on next Analysis page visit.")


def _export_zip_bundle() -> Path:
    """Create ZIP with all available outputs."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = OUTPUT_DIR / f"mbsi_export_{stamp}.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if st.session_state.reconstructed is not None:
            h5 = OUTPUT_DIR / "_tmp_recon.h5ad"
            st.session_state.reconstructed.write_h5ad(h5)
            zf.write(h5, "reconstructed.h5ad")
            h5.unlink(missing_ok=True)
        metrics_path = save_metrics(f"metrics_{stamp}.json")
        zf.write(metrics_path, metrics_path.name)
        snap = save_snapshot(f"snapshot_{stamp}.json")
        zf.write(snap, snap.name)
    zip_path.write_bytes(buf.getvalue())
    return zip_path
