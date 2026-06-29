"""Ground session outputs for AI review — findings-first."""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from app.components.safe import safe_get
from mbsi.graph.query import get_path_to_outcome, get_related_findings
from mbsi.reports.registry import get_registered_outputs


def collect_grounded_outputs() -> Dict[str, Any]:
    """Collect findings, evidence, confidence, notebook — not raw adata."""
    dos_findings = list(st.session_state.get("findings", []))
    dos_evidence = list(st.session_state.get("evidence", []))
    discovery = st.session_state.get("discovery_results") or {}

    if not dos_findings and discovery.get("findings"):
        dos_findings = discovery["findings"]
    if not dos_evidence and discovery.get("evidence"):
        dos_evidence = discovery["evidence"]

    grounded: Dict[str, Any] = {
        "registered": get_registered_outputs(),
        "last_run": st.session_state.get("last_run"),
        "warnings": list(st.session_state.get("saas_warnings", [])),
        "findings": dos_findings,
        "evidence": dos_evidence,
        "discovery_graph": discovery.get("discovery_graph") or st.session_state.get("discovery_graph"),
        "validation_recommendations": discovery.get("validation_recommendations", []),
        "notebook": st.session_state.get("notebook_runs") or [],
    }

    bench = st.session_state.get("benchmark_results")
    if bench:
        grounded["benchmark"] = {
            "readiness_score": safe_get(bench, "readiness_score"),
            "leaderboard_top": _top_leaderboard(bench),
            "benchmark_mode": bench.get("benchmark_mode"),
            "benchmark_support": _benchmark_support_for_findings(dos_findings, bench),
        }
    comm = st.session_state.get("communication_results")
    if comm:
        grounded["communication"] = {"top_pathway": comm.get("top_pathway")}
    tme = st.session_state.get("tme_results")
    if tme:
        summary = tme.get("summary")
        grounded["tme"] = {"niche_count": len(summary) if summary is not None else 0}
    if discovery:
        grounded["discovery"] = {
            "status": discovery.get("status"),
            "warnings": discovery.get("warnings", []),
            "n_findings": len(dos_findings),
            "run_id": discovery.get("run_id"),
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


def _benchmark_support_for_findings(findings: List[Dict], bench: Dict[str, Any]) -> float:
    if not findings or not bench:
        return 0.0
    lb = bench.get("leaderboard")
    if lb is None or not hasattr(lb, "empty") or lb.empty:
        return 0.0
    return float(lb.iloc[0].get("gene_pearson", 0)) * 100.0


def get_finding_context(finding_id: str) -> Dict[str, Any]:
    """Return graph path and related findings for a finding_id."""
    graph = st.session_state.get("discovery_graph") or {}
    if not graph:
        disc = st.session_state.get("discovery_results") or {}
        graph = disc.get("discovery_graph") or {}
    return {
        "path": get_path_to_outcome(finding_id, graph),
        "related": get_related_findings(finding_id, graph),
    }
