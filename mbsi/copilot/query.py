"""Copilot query engine — answers from computed analysis state only."""

from typing import Any, Dict, List

QUERY_TEMPLATES = [
    "Show tumor-stroma boundary regions.",
    "Show immune-excluded niches.",
    "Which markers define reconstructed compartments?",
    "Which genes show strongest spatial leakage?",
    "Which regions may be platinum-resistant?",
    "Simulate PD-1 blockade.",
    "Export Nature-style figure package.",
]


def answer_tissue_query(query: str, analysis_state: Dict[str, Any]) -> str:
    """
    Answer tissue query using only precomputed analysis_state.

    No external LLM — template matching on computed outputs.
    """
    q = query.lower()
    if "boundary" in q or "tumor-stroma" in q:
        b = analysis_state.get("boundaries", {})
        score = b.get("mean_boundary_score", "N/A")
        return f"Boundary analysis (reconstruction estimate): mean boundary score = {score}. {b.get('note', '')}"
    if "immune" in q and "excl" in q:
        ex = analysis_state.get("immune_exclusion", {})
        return f"Immune exclusion zones (computational hypothesis): mean score = {ex.get('mean', 'N/A')}."
    if "compartment" in q or "marker" in q:
        comps = analysis_state.get("compartments", {})
        return f"Compartments detected: {comps.get('labels', 'Run segmentation first')}."
    if "leakage" in q:
        leak = analysis_state.get("leakage_score", "N/A")
        return f"Spatial leakage score (computational hypothesis): {leak}."
    if "resistant" in q or "platinum" in q:
        r = analysis_state.get("digital_twin", {}).get("resistance_score", "N/A")
        return f"Predicted resistance score (simulation): {r}. Requires experimental validation."
    if "pd-1" in q or "simulate" in q:
        sim = analysis_state.get("treatment_simulation", {})
        return f"PD-1 blockade simulation: {sim.get('PD-1 blockade', sim)}. Not for clinical use."
    if "export" in q or "figure" in q:
        return "Use Export Report page to download h5ad, figures, HTML report, and reproducibility bundle."
    if "metrics" in q or "validation" in q:
        m = analysis_state.get("metrics", {})
        return f"Validation metrics: {m}"
    return (
        "I can answer from computed outputs only. Try: boundary regions, immune exclusion, "
        "compartments, leakage, resistance, PD-1 simulation, or export figures."
    )
