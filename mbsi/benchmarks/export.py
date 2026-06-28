"""Benchmark Hub export utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


def export_benchmark_hub(
    hub_output: Dict[str, Any],
    out_dir: Path = Path("data/outputs"),
) -> Path:
    """Export benchmark_results.csv, benchmark_report (PDF or HTML), benchmark_methods.txt."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = hub_output.get("results", [])
    leaderboard = hub_output.get("leaderboard")
    if isinstance(leaderboard, pd.DataFrame):
        df = leaderboard.copy()
    else:
        df = pd.DataFrame(results)

    csv_path = out_dir / "benchmark_results.csv"
    df.to_csv(csv_path, index=False)

    methods_path = out_dir / "benchmark_methods.txt"
    lines = [
        "MBSI Studio — Benchmark Methods",
        "=" * 40,
        hub_output.get("vc_banner", ""),
        "",
        hub_output.get("guardrail", ""),
        "",
        f"Platform: {hub_output.get('platform', 'unknown')}",
        f"Seed: {hub_output.get('seed', 42)}",
        "",
    ]
    for row in results:
        lines.append(
            f"- {row.get('method')}: type={row.get('method_type')} status={row.get('status')}"
        )
        if row.get("notes"):
            lines.append(f"  notes: {row['notes']}")
    methods_path.write_text("\n".join(lines))

    report_html = _build_html_report(hub_output, df)
    html_path = out_dir / "benchmark_report.html"
    html_path.write_text(report_html)

    pdf_path = out_dir / "benchmark_report.pdf"
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        y = 750
        for line in hub_output.get("summary_text", "").split("\n")[:40]:
            c.drawString(50, y, line[:90])
            y -= 14
            if y < 50:
                c.showPage()
                y = 750
        c.save()
    except ImportError:
        pdf_path = html_path  # fallback noted in return

    meta = {
        "platform": hub_output.get("platform"),
        "seed": hub_output.get("seed"),
        "n_methods": len(results),
        "exports": {
            "csv": str(csv_path),
            "html": str(html_path),
            "methods": str(methods_path),
        },
    }
    (out_dir / "benchmark_meta.json").write_text(json.dumps(meta, indent=2))
    return out_dir


def _build_html_report(hub_output: Dict[str, Any], df: pd.DataFrame) -> str:
    rows = ""
    if not df.empty:
        for _, r in df.iterrows():
            rows += (
                f"<tr><td>{r.get('rank', '')}</td><td>{r.get('method', '')}</td>"
                f"<td>{r.get('method_type', '')}</td>"
                f"<td>{r.get('gene_pearson', 0):.3f}</td>"
                f"<td>{r.get('rmse', 0):.3f}</td>"
                f"<td>{r.get('runtime_sec', 0):.2f}</td></tr>"
            )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>MBSI Benchmark Report</title>
<style>body{{background:#0d1828;color:#f4f7fb;font-family:sans-serif;padding:24px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #22314a;padding:8px}}</style>
</head><body>
<h1>MBSI Studio Benchmark Hub Report</h1>
<p><em>{hub_output.get('vc_banner', '')}</em></p>
<p>{hub_output.get('guardrail', '')}</p>
<pre>{hub_output.get('summary_text', '')}</pre>
<table><tr><th>Rank</th><th>Method</th><th>Type</th><th>Pearson</th><th>RMSE</th><th>Runtime(s)</th></tr>
{rows}</table></body></html>"""
