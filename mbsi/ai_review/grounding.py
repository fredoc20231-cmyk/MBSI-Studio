"""Ground session outputs for AI review."""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from app.components.safe import safe_get
from mbsi.reports.registry import get_registered_outputs


def collect_grounded_outputs() -> Dict[str, Any]:
    """Collect only registered and session-backed outputs (no hallucination source)."""
    grounded: Dict[str, Any] = {
        "registered": get_registered_outputs(),
        "last_run": st.session_state.get("last_run"),
        "warnings": list(st.session_state.get("saas_warnings", [])),
        "findings": list(st.session_state.get("saas_findings", [])),
    }
    bench = st.session_state.get("benchmark_results")
    if bench:
        grounded["benchmark"] = {
            "readiness_score": safe_get(bench, "readiness_score"),
            "leaderboard_top": _top_leaderboard(bench),
        }
    comm = st.session_state.get("communication_results")
    if comm:
        grounded["communication"] = {"top_pathway": comm.get("top_pathway")}
    tme = st.session_state.get("tme_results")
    if tme:
        summary = tme.get("summary")
        grounded["tme"] = {"niche_count": len(summary) if summary is not None else 0}
    disc = st.session_state.get("discovery_results")
    if disc:
        grounded["discovery"] = {
            "status": disc.get("status"),
            "warnings": disc.get("warnings", []),
        }
    return grounded


def _top_leaderboard(bench: Dict[str, Any]) -> str:
    lb = safe_get(bench, "leaderboard")
    if lb is None or not hasattr(lb, "empty") or lb.empty:
        return "N/A"
    row = lb.iloc[0]
    method = row.get("method", "unknown")
    pearson = row.get("gene_pearson", 0)
    return f"{method} (Pearson={pearson:.3f})"
