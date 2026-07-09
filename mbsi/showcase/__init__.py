"""MBSI Studio flagship disease showcases.

Status: DEVELOPER UI ONLY — requires DEVELOPER_MODE=true; synthetic showcase data.
See docs/RESEARCH_MODULES.md.
"""

from mbsi.showcase.ovarian_hgsc import (
    make_ovarian_showcase_adata,
    run_ovarian_showcase_pipeline,
    export_ovarian_showcase,
    score_resistance_programs,
    SHOWCASE_GUARDRAIL,
)
from mbsi.showcase.report import generate_ovarian_showcase_report

__all__ = [
    "make_ovarian_showcase_adata",
    "run_ovarian_showcase_pipeline",
    "export_ovarian_showcase",
    "generate_ovarian_showcase_report",
    "score_resistance_programs",
    "SHOWCASE_GUARDRAIL",
]
