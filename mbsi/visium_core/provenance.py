"""Phase 6 — provenance capture, evidence tiers and blocked-analysis states."""

from __future__ import annotations

import hashlib
import inspect
import platform
from datetime import datetime, timezone
from importlib import metadata
from typing import Any, Callable, Dict, Iterable, List, Optional

EVIDENCE_TIERS = ("observed", "statistically_supported", "hypothesis", "blocked")


class BlockedAnalysis(Exception):
    """Raised when an analysis must not run (missing data, replicates or libraries)."""

    def __init__(self, reason: str, requirement: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.requirement = requirement


def package_versions(names: Iterable[str]) -> Dict[str, Optional[str]]:
    out: Dict[str, Optional[str]] = {}
    for name in names:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def code_hash(fn: Callable[..., Any]) -> str:
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        src = repr(fn)
    return hashlib.sha256(src.encode()).hexdigest()[:16]


def provenance(
    module: str,
    fn: Callable[..., Any],
    params: Dict[str, Any],
    packages: Iterable[str],
    tier: str,
    caveats: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    if tier not in EVIDENCE_TIERS:
        raise ValueError(f"Unknown evidence tier {tier}")
    return {
        "module": module,
        "applied_params": params,
        "tool_versions": {"python": platform.python_version(), **package_versions(packages)},
        "code_hash": code_hash(fn),
        "evidence_tier": tier,
        # Each caveat names the exact output field it qualifies.
        "caveats": caveats or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def blocked(module: str, exc: BlockedAnalysis, params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "blocked",
        "module": module,
        "blocked_reason": exc.reason,
        "requirement": exc.requirement,
        "provenance": {"module": module, "applied_params": params, "evidence_tier": "blocked"},
    }


def require(package: str, requirement: str) -> Any:
    import importlib

    try:
        return importlib.import_module(package)
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise BlockedAnalysis(f"Python package '{package}' is not installed on the scientific service.", requirement) from exc


def facts_gate(report_claims: List[Dict[str, Any]], results: Dict[str, Any]) -> List[str]:
    """Return violations: each report claim must cite an output field that exists and is not blocked."""
    problems = []
    for claim in report_claims:
        src = results.get(claim.get("source_module", ""))
        if not src or src.get("status") != "complete":
            problems.append(f"Claim '{claim.get('text')}' cites a missing or blocked result.")
        elif claim.get("field") not in src.get("outputs", {}):
            problems.append(f"Claim '{claim.get('text')}' cites unknown field '{claim.get('field')}'.")
    return problems
