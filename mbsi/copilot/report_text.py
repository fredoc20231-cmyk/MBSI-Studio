"""Methods and results text for reports."""

from typing import Any, Dict


def generate_methods_text(parameters: Dict[str, Any]) -> str:
    return (
        "MBSI Studio reconstruction used physics-aware optimal transport with sheaf regularization. "
        f"Parameters: {parameters}. Advanced modules produce computational hypotheses only."
    )


def generate_results_text(metrics: Dict[str, Any]) -> str:
    lines = ["Results (reconstruction estimates / computational hypotheses):"]
    for k, v in metrics.items():
        if isinstance(v, (int, float)):
            lines.append(f"  {k}: {v:.4f}")
        elif v is not None:
            lines.append(f"  {k}: {v}")
    lines.append("Requires experimental validation.")
    return "\n".join(lines)
