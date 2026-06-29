"""Finding type ontology for MBSI Discovery Operating System."""

from __future__ import annotations

from enum import Enum


class FindingType(str, Enum):
    IMMUNE_EXCLUSION = "immune_exclusion"
    CAF_BARRIER = "caf_barrier"
    LR_PATHWAY = "lr_pathway"
    HYPOXIA_NICHE = "hypoxia_niche"
    BIOMARKER = "biomarker"
    CAUSAL_DRIVER = "causal_driver"
    RECONSTRUCTION = "reconstruction"
    NICHE = "niche"
    PATHWAY = "pathway"
    TME_PROGRAM = "tme_program"
    COMMUNICATION = "communication"
    BENCHMARK = "benchmark"
    UNKNOWN = "unknown"


FINDING_TYPE_LABELS = {
    FindingType.IMMUNE_EXCLUSION: "Immune Exclusion",
    FindingType.CAF_BARRIER: "CAF Barrier",
    FindingType.LR_PATHWAY: "Ligand-Receptor Pathway",
    FindingType.HYPOXIA_NICHE: "Hypoxia Niche",
    FindingType.BIOMARKER: "Biomarker",
    FindingType.CAUSAL_DRIVER: "Causal Driver",
    FindingType.RECONSTRUCTION: "Reconstruction Quality",
    FindingType.NICHE: "Spatial Niche",
    FindingType.PATHWAY: "Signaling Pathway",
    FindingType.TME_PROGRAM: "TME Program",
    FindingType.COMMUNICATION: "Cell Communication",
    FindingType.BENCHMARK: "Benchmark Result",
    FindingType.UNKNOWN: "Finding",
}
