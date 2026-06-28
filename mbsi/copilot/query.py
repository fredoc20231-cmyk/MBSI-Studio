"""Copilot query engine — answers from computed analysis state only."""

from typing import Any, Dict, List

ALLOWED_SOURCES = [
    "metrics",
    "benchmark_results",
    "communication_results",
    "tme_results",
    "analysis_state",
    "discovery_results",
]

QUERY_TEMPLATES = [
    "Show tumor-stroma boundary regions.",
    "Show immune-excluded niches.",
    "Which markers define reconstructed compartments?",
    "Which genes show strongest spatial leakage?",
    "Which regions may be platinum-resistant?",
    "What is the top communication pathway?",
    "Which benchmark method performed best?",
    "Summarize TME niche findings.",
    "Export Nature-style figure package.",
]


def build_analysis_context(session_state: Dict[str, Any]) -> Dict[str, Any]:
    """Gather allowed sources from session-like dict."""
    ctx = {}
    for src in ALLOWED_SOURCES:
        val = session_state.get(src)
        if val is not None:
            ctx[src] = val
    return ctx


def answer_tissue_query(query: str, analysis_state: Dict[str, Any]) -> str:
    """Answer query using only precomputed outputs."""
    q = query.lower()

    if "benchmark" in q or "method" in q and "best" in q:
        bench = analysis_state.get("benchmark_results", {})
        lb = bench.get("leaderboard")
        if lb is not None and hasattr(lb, "empty") and not lb.empty:
            top = lb.iloc[0]
            return f"Benchmark (computational): top method {top['method']} Pearson={top.get('gene_pearson', 0):.3f}. {bench.get('guardrail', '')}"
        return "Run Benchmark Hub first."

    if "communication" in q or "pathway" in q or "cxcl12" in q:
        comm = analysis_state.get("communication_results", {})
        top = comm.get("top_pathway", "N/A")
        return f"Top communication pathway (hypothesis): {top}. {comm.get('guardrail', '')}"

    if "tme" in q or "niche" in q:
        tme = analysis_state.get("tme_results", {})
        summary = tme.get("summary")
        if summary is not None and hasattr(summary, "empty") and not summary.empty:
            lines = [f"- {r['niche_type']}: {int(r['n_spots_detected'])} spots" for _, r in summary.iterrows()]
            return "TME niches (computational hypothesis):\n" + "\n".join(lines)
        return "Run TME analysis first."

    if "boundary" in q or "tumor-stroma" in q:
        b = analysis_state.get("analysis_state", {}).get("boundaries", analysis_state.get("boundaries_result", {}))
        score = b.get("mean_boundary_score", "N/A") if isinstance(b, dict) else "N/A"
        return f"Boundary analysis (reconstruction estimate): mean score = {score}."

    if "immune" in q and "excl" in q:
        tme = analysis_state.get("tme_results", {})
        ie = tme.get("niches", {}).get("immune_exclusion", {})
        return f"Immune exclusion (hypothesis): {ie.get('n_niches', 'N/A')} spots, mean score {ie.get('mean_score', 'N/A')}."

    if "resistant" in q or "platinum" in q:
        dt = analysis_state.get("digital_twin", analysis_state.get("analysis_state", {}).get("digital_twin", {}))
        r = dt.get("resistance_score", "N/A") if isinstance(dt, dict) else "N/A"
        return f"Predicted resistance (simulation): {r}. Requires experimental validation."

    if "export" in q or "figure" in q:
        return "Use Discovery Engine or Export page for biopharma report and CSV bundle."

    if "metrics" in q or "validation" in q:
        return f"Validation metrics: {analysis_state.get('metrics', {})}"

    return (
        "I answer from computed outputs only. Try: benchmark method, communication pathway, "
        "TME niches, immune exclusion, boundary regions, resistance, or export report."
    )
