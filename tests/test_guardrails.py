"""Tests for mbsi.guardrails module (0% -> target ~100%)."""

from mbsi.guardrails import (
    CAUSAL_WARNING,
    COMPUTATIONAL_HYPOTHESIS,
    GUARDRAIL_BANNER,
    RECONSTRUCTION_ESTIMATE,
    REQUIRES_VALIDATION,
    SIMULATION_WARNING,
)


def test_constants_are_nonempty_strings():
    for const in (
        RECONSTRUCTION_ESTIMATE,
        COMPUTATIONAL_HYPOTHESIS,
        REQUIRES_VALIDATION,
        GUARDRAIL_BANNER,
        CAUSAL_WARNING,
        SIMULATION_WARNING,
    ):
        assert isinstance(const, str)
        assert len(const) > 0


def test_guardrail_banner_contains_components():
    assert RECONSTRUCTION_ESTIMATE in GUARDRAIL_BANNER
    assert COMPUTATIONAL_HYPOTHESIS in GUARDRAIL_BANNER
    assert REQUIRES_VALIDATION in GUARDRAIL_BANNER


def test_causal_warning_mentions_validation():
    assert "validation" in CAUSAL_WARNING.lower()


def test_simulation_warning_mentions_clinical():
    assert "clinical" in SIMULATION_WARNING.lower()
