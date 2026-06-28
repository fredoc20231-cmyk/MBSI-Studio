"""TME intelligence report — wraps unified biomarker report."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from mbsi.tme.pipeline import TME_GUARDRAIL


def generate_tme_report(results: Dict[str, Any], out_dir: Path = Path("data/outputs")) -> Path:
    """Generate TME-focused HTML report."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "tme_intelligence_report.html"
    summary = results.get("summary")
    rows = ""
    if summary is not None and not summary.empty:
        for _, r in summary.iterrows():
            rows += f"<tr><td>{r['niche_type']}</td><td>{int(r['n_spots_detected'])}</td><td>{r['mean_score']:.3f}</td></tr>"
    html = f"""<!DOCTYPE html><html><body style="background:#0d1828;color:#f4f7fb;font-family:sans-serif;padding:24px">
<h1>TME Intelligence Report</h1><p><em>{TME_GUARDRAIL}</em></p>
<table border=1 cellpadding=8 style="border-color:#22314a"><tr><th>Niche</th><th>Spots</th><th>Score</th></tr>{rows}</table>
</body></html>"""
    path.write_text(html)
    return path
