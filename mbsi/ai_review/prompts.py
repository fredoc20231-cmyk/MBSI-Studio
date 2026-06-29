"""Prompt templates for rule-based AI review."""

GUARDRAIL = (
    "This assistant uses only registered pipeline outputs. "
    "It is not clinical decision support."
)

TEMPLATES = {
    "benchmark": "Benchmark readiness: {readiness}. Top method: {top}. Benchmark support: {support}.",
    "communication": "Top communication pathway: {pathway}.",
    "tme": "TME niches detected: {count}.",
    "discovery": "Discovery status: {status}. Findings: {n_findings}.",
    "warnings": "Recent warnings ({n}): {list}",
    "findings": "Top findings ({n}): {list}",
    "confidence": "Confidence-ranked findings: {list}",
    "evidence": "Evidence items ({n}): {list}",
    "validation": "Validation recommendations: {list}",
    "graph": "Finding path to outcome: {path}. Related findings: {related}.",
    "default": "Last run: {last_run}. {n_findings} findings, {n_fig} figures, {n_tbl} tables.",
}
