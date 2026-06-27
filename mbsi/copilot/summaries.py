"""Biological summary generation."""

from typing import Any, Dict


def generate_biological_summary(analysis_results: Dict[str, Any]) -> str:
    """Generate summary text from analysis results."""
    lines = ["## Biological Summary (Computational Hypothesis)", ""]
    if "n_cells" in analysis_results:
        lines.append(f"- Reconstructed cells: {analysis_results['n_cells']} (reconstruction estimate)")
    if "compartments" in analysis_results:
        lines.append(f"- Compartments: {analysis_results['compartments']}")
    if "leakage_score" in analysis_results:
        lines.append(f"- Boundary leakage score: {analysis_results['leakage_score']:.4f}")
    if "metrics" in analysis_results:
        m = analysis_results["metrics"]
        if isinstance(m, dict) and "pearson_correlation" in m:
            lines.append(f"- Validation Pearson r: {m['pearson_correlation']:.4f}")
    lines.append("")
    lines.append("*Requires experimental validation. Not for clinical diagnosis or treatment.*")
    return "\n".join(lines)
