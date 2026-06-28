"""Communication intelligence HTML report."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from mbsi.communication.ligand_receptor import COMMUNICATION_GUARDRAIL


def generate_communication_report(results: Dict[str, Any], out_dir: Path = Path("data/outputs")) -> Path:
    """Export communication analysis HTML report."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "communication_report.html"

    rankings = results.get("pathway_rankings")
    rows = ""
    if rankings is not None and not rankings.empty:
        for _, r in rankings.head(10).iterrows():
            rows += f"<tr><td>{r.get('pathway_name', r.get('pathway'))}</td><td>{r.get('score', 0):.3f}</td><td>{r.get('probability', 0):.3f}</td></tr>"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Communication Report</title>
<style>body{{background:#0d1828;color:#f4f7fb;font-family:sans-serif;padding:24px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #22314a;padding:8px}}</style>
</head><body>
<h1>Communication Intelligence Report</h1>
<p><em>{COMMUNICATION_GUARDRAIL}</em></p>
<p>Top pathway: <strong>{results.get('top_pathway', 'N/A')}</strong></p>
<table><tr><th>Pathway</th><th>Score</th><th>Probability</th></tr>{rows}</table>
</body></html>"""
    path.write_text(html)
    return path
