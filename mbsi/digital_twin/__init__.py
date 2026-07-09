"""Tissue digital twin.

Status: EXPERIMENTAL — legacy API routes only; not Milestone 1 production.
See docs/RESEARCH_MODULES.md.
"""

from mbsi.digital_twin.state import build_tissue_digital_twin
from mbsi.digital_twin.treatment import TREATMENTS
from mbsi.digital_twin.simulate import simulate_treatment, compare_treatment_scenarios

__all__ = [
    "build_tissue_digital_twin",
    "simulate_treatment",
    "compare_treatment_scenarios",
    "TREATMENTS",
]
