"""Simulate future tissue states."""

from typing import Any, Dict

import numpy as np


def simulate_tissue_future(state: Dict[str, Any], steps: int = 5) -> Dict:
    """
    Simple forward simulation of compartment/marker/resistance trajectories.
    """
    compartments = dict(state.get("compartments", {"tumor": 0.4, "stroma": 0.3, "immune": 0.2, "necrosis": 0.1}))
    resistance = float(state.get("resistance_score", 0.3))
    trajectory = [dict(compartments)]

    for _ in range(steps):
        # Simple dynamics: tumor expands, immune fluctuates, resistance drifts
        compartments["tumor"] = min(0.9, compartments.get("tumor", 0.4) * 1.02)
        compartments["immune"] = max(0.05, compartments.get("immune", 0.2) * 0.98)
        compartments["stroma"] = 1.0 - sum(compartments.values()) + compartments.get("stroma", 0.3)
        compartments["stroma"] = max(0.05, compartments["stroma"])
        resistance = min(1.0, resistance * 1.01)
        trajectory.append(dict(compartments))

    return {
        "trajectory": trajectory,
        "resistance_score": resistance,
        "steps": steps,
        "warning": "Simulation/hypothesis generation only. Not for clinical use.",
    }
