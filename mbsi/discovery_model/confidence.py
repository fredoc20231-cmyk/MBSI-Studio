"""Confidence level mapping for findings."""

from __future__ import annotations


def confidence_level(score: float) -> str:
    """Map 0-100 confidence score to categorical level."""
    if score >= 75:
        return "High"
    if score >= 50:
        return "Moderate"
    if score >= 25:
        return "Exploratory"
    return "Hypothesis"
