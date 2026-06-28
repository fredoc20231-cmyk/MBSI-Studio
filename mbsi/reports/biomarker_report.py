"""Unified spatial biomarker report across discovery modules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

BIOMARKER_DISCLAIMER = (
    "This report is a computational research output. It is not a diagnostic test, "
    "treatment recommendation, or clinical decision support system. Findings require "
    "independent biological and clinical validation."
)


def generate_biomarker_report_text(
    benchmark_results: Optional[Dict[str, Any]] = None,
    communication_results: Optional[Dict[str, Any]] = None,
    tme_results: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate plain-text biomarker report narrative."""
    lines = [
        "MBSI Studio — Spatial Biomarker Report",
        "=" * 50,
        BIOMARKER_DISCLAIMER,
        "",
        "All findings below are computational hypotheses.",
        "",
    ]

    if benchmark_results:
        lb = benchmark_results.get("leaderboard")
        lines.append("## Benchmark Hub")
        lines.append(f"Readiness score: {benchmark_results.get('readiness_score', 'N/A')}")
        if lb is not None and not lb.empty:
            top = lb.iloc[0]
            lines.append(f"Top method: {top.get('method')} (Pearson={top.get('gene_pearson', 0):.3f})")
        lines.append("")

    if communication_results:
        lines.append("## Communication Intelligence")
        lines.append(f"Top pathway: {communication_results.get('top_pathway', 'N/A')}")
        rankings = communication_results.get("pathway_rankings")
        if rankings is not None and not rankings.empty:
            for _, r in rankings.head(3).iterrows():
                lines.append(f"  - {r.get('pathway_name', r.get('pathway'))}: score={r.get('score', 0):.3f}")
        lines.append("")

    if tme_results:
        lines.append("## TME Intelligence")
        summary = tme_results.get("summary")
        if summary is not None and not summary.empty:
            for _, r in summary.iterrows():
                lines.append(f"  - {r['niche_type']}: {int(r['n_spots_detected'])} spots, score={r['mean_score']:.3f}")
        lines.append("")

    lines.append("End of report.")
    return "\n".join(lines)


def generate_spatial_biomarker_report(
    benchmark_results: Optional[Dict[str, Any]] = None,
    communication_results: Optional[Dict[str, Any]] = None,
    tme_results: Optional[Dict[str, Any]] = None,
    out_dir: Path = Path("data/outputs"),
) -> Path:
    """Generate unified HTML spatial biomarker report."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "spatial_biomarker_report.html"

    text = generate_biomarker_report_text(benchmark_results, communication_results, tme_results)

    bench_rows = ""
    if benchmark_results and benchmark_results.get("leaderboard") is not None:
        lb = benchmark_results["leaderboard"]
        if not lb.empty:
            for _, r in lb.head(5).iterrows():
                bench_rows += f"<tr><td>{r.get('method')}</td><td>{r.get('gene_pearson', 0):.3f}</td><td>{r.get('rmse', 0):.3f}</td></tr>"

    comm_rows = ""
    if communication_results:
        rankings = communication_results.get("pathway_rankings")
        if rankings is not None and not rankings.empty:
            for _, r in rankings.head(5).iterrows():
                comm_rows += f"<tr><td>{r.get('pathway_name', r.get('pathway'))}</td><td>{r.get('score', 0):.3f}</td></tr>"

    tme_rows = ""
    if tme_results:
        summary = tme_results.get("summary")
        if summary is not None and not summary.empty:
            for _, r in summary.iterrows():
                tme_rows += f"<tr><td>{r['niche_type']}</td><td>{int(r['n_spots_detected'])}</td><td>{r['mean_score']:.3f}</td></tr>"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Spatial Biomarker Report</title>
<style>
body{{background:#0d1828;color:#f4f7fb;font-family:Georgia,serif;padding:32px;max-width:960px;margin:auto;line-height:1.6}}
h1{{color:#4f7cff}}h2{{color:#ff4f7b;margin-top:28px}}
.guardrail{{background:#07111f;border-left:4px solid #ffb020;padding:12px 16px;margin:20px 0;color:#9aa7b8;font-style:italic}}
table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #22314a;padding:8px}}th{{background:#07111f}}
pre{{background:#07111f;padding:16px;border-radius:8px;overflow-x:auto;font-size:0.85rem}}
</style></head><body>
<h1>Biopharma Discovery Engine — Spatial Biomarker Report</h1>
<div class="guardrail">{BIOMARKER_DISCLAIMER}</div>
<h2>Benchmark Leaderboard</h2>
<table><tr><th>Method</th><th>Pearson</th><th>RMSE</th></tr>{bench_rows or '<tr><td colspan=3>No benchmark data</td></tr>'}</table>
<h2>Communication Pathways</h2>
<table><tr><th>Pathway</th><th>Score</th></tr>{comm_rows or '<tr><td colspan=2>No communication data</td></tr>'}</table>
<h2>TME Niches</h2>
<table><tr><th>Niche</th><th>Spots</th><th>Score</th></tr>{tme_rows or '<tr><td colspan=3>No TME data</td></tr>'}</table>
<h2>Full Narrative</h2>
<pre>{text}</pre>
</body></html>"""

    html_path.write_text(html)
    (out_dir / "biomarker_report_summary.json").write_text(
        json.dumps({
            "disclaimer": BIOMARKER_DISCLAIMER,
            "has_benchmark": benchmark_results is not None,
            "has_communication": communication_results is not None,
            "has_tme": tme_results is not None,
        }, indent=2)
    )
    return html_path
