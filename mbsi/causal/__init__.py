"""Spatial causal inference.

Status: EXPERIMENTAL — legacy API and Discovery workspace; research-stage.
See docs/RESEARCH_MODULES.md.
"""

from mbsi.causal.dag import build_spatial_causal_dag
from mbsi.causal.interventions import run_spatial_intervention
from mbsi.causal.attribution import rank_causal_drivers, compute_spatial_attribution

__all__ = [
    "build_spatial_causal_dag",
    "run_spatial_intervention",
    "rank_causal_drivers",
    "compute_spatial_attribution",
]
