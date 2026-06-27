"""Treatment simulation for digital twin."""

from typing import Any, Dict, List

from mbsi.digital_twin.treatment import TREATMENTS


def simulate_treatment(twin: Dict[str, Any], treatment_name: str) -> Dict[str, Any]:
    """Simulate single treatment effect on twin state."""
    tx = TREATMENTS.get(treatment_name, TREATMENTS["untreated"])
    comps = dict(twin.get("compartments", {}))
    tumor = comps.get("tumor", 0.4) * (1 - tx["tumor_kill"])
    immune = min(0.6, comps.get("immune", 0.2) + tx["immune_boost"])
    comps["tumor"] = max(0.05, tumor)
    comps["immune"] = max(0.05, immune)
    resistance = twin.get("resistance_score", 0.3) + tx["resistance_change"]

    return {
        "treatment": treatment_name,
        "predicted_compartments": comps,
        "immune_infiltration_change": tx["immune_boost"],
        "resistance_score_change": tx["resistance_change"],
        "predicted_resistance": float(max(0, min(1, resistance))),
        "uncertainty_score": twin.get("uncertainty", 0.15) + 0.05,
        "warning": "Simulation/hypothesis generation only. Not for clinical use.",
    }


def compare_treatment_scenarios(
    twin: Dict[str, Any],
    treatments: List[str],
) -> Dict[str, Any]:
    """Compare multiple treatment scenarios."""
    results = {t: simulate_treatment(twin, t) for t in treatments}
    return {"scenarios": results, "warning": "Computational hypothesis - Requires experimental validation"}
