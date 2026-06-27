"""Scientific guardrail labels for advanced MBSI outputs."""

RECONSTRUCTION_ESTIMATE = "Reconstruction estimate"
COMPUTATIONAL_HYPOTHESIS = "Computational hypothesis"
REQUIRES_VALIDATION = "Requires experimental validation"

GUARDRAIL_BANNER = (
    f"{RECONSTRUCTION_ESTIMATE} | {COMPUTATIONAL_HYPOTHESIS} | {REQUIRES_VALIDATION}"
)

CAUSAL_WARNING = (
    "Causal outputs are computational hypotheses requiring experimental validation."
)

SIMULATION_WARNING = (
    "Simulation outputs are hypothesis generation only. "
    "Not for clinical diagnosis or treatment recommendation."
)
