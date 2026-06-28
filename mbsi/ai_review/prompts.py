"""Prompt templates for rule-based AI review."""

GUARDRAIL = (
    "This assistant uses only registered pipeline outputs. "
    "It is not clinical decision support."
)

TEMPLATES = {
    "benchmark": "Benchmark readiness: {readiness}. Top method: {top}.",
    "communication": "Top communication pathway: {pathway}.",
    "tme": "TME niches detected: {count}.",
    "discovery": "Discovery status: {status}.",
    "warnings": "Recent warnings ({n}): {list}",
    "findings": "Top findings ({n}): {list}",
    "default": "Last run: {last_run}. Registered outputs: {n_fig} figures, {n_tbl} tables.",
}
