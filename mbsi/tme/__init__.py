"""Tumor microenvironment intelligence."""

from mbsi.tme.pipeline import run_tme_analysis, export_tme_results, TME_GUARDRAIL
from mbsi.tme.biomarker_report import generate_spatial_biomarker_report
from mbsi.tme.demo import make_tme_demo_adata
from mbsi.tme.immune_exclusion import detect_immune_exclusion
from mbsi.tme.tls import detect_tls_niches
from mbsi.tme.caf_barriers import detect_caf_barriers
from mbsi.tme.angiogenesis import score_angiogenic_regions
from mbsi.tme.hypoxia import score_hypoxic_niches
from mbsi.tme.invasion import detect_invasive_fronts

__all__ = [
    "run_tme_analysis",
    "export_tme_results",
    "generate_spatial_biomarker_report",
    "make_tme_demo_adata",
    "detect_immune_exclusion",
    "detect_tls_niches",
    "detect_caf_barriers",
    "score_angiogenic_regions",
    "score_hypoxic_niches",
    "detect_invasive_fronts",
    "TME_GUARDRAIL",
]
