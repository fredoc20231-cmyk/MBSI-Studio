"""Module compatibility matrix from ingested AnnData."""

from __future__ import annotations

from typing import Any, Dict, Optional

import anndata as ad

from mbsi.io.detect import PlatformDetection


def _entry(status: str, reason: str = "") -> Dict[str, str]:
    out = {"status": status}
    if reason:
        out["reason"] = reason
    return out


def get_compatibility_matrix(
    adata: Optional[ad.AnnData],
    detection: Optional[PlatformDetection] = None,
) -> Dict[str, Dict[str, str]]:
    """Return per-module availability based on data contract."""
    if adata is None:
        return {
            "upload": _entry("available"),
            "qc": _entry("unavailable", "no data loaded"),
            "spatial_analysis": _entry("unavailable", "no data loaded"),
            "mbsi_reconstruction": _entry("unavailable", "no data loaded"),
            "benchmark_hub": _entry("unavailable", "no data loaded"),
            "communication": _entry("unavailable", "no data loaded"),
            "tme": _entry("unavailable", "no data loaded"),
            "discovery": _entry("warn", "demo pipeline only without upload"),
            "report": _entry("available"),
        }

    has_spatial = "spatial" in adata.obsm
    n_obs = adata.n_obs
    n_vars = adata.n_vars
    has_cell_types = "cell_type" in adata.obs or "cluster" in adata.obs
    platform = (detection or {}).get("platform") or adata.uns.get("mbsi_platform", "unknown")
    has_sc_ref = adata.uns.get("single_cell_reference") is not None

    matrix: Dict[str, Dict[str, str]] = {
        "upload": _entry("available"),
        "qc": _entry("available" if has_spatial and n_obs >= 5 else "unavailable", "needs spatial coords"),
        "spatial_analysis": _entry("available" if has_spatial and n_vars >= 20 else "warn", "low gene count"),
        "mbsi_reconstruction": _entry(
            "available" if has_spatial and n_obs >= 20 else "warn",
            "reconstruction works best with ≥20 spots",
        ),
        "benchmark_hub": _entry(
            "unavailable" if not has_sc_ref else "available",
            "requires single-cell ground truth reference",
        ),
        "communication": _entry(
            "available" if n_obs >= 10 and n_vars >= 30 else "warn",
            "L-R scoring needs sufficient genes/spots",
        ),
        "tme": _entry(
            "available" if has_cell_types or n_obs >= 15 else "warn",
            "niche detection improves with cell type labels",
        ),
        "discovery": _entry(
            "warn" if platform in ("unknown", "incomplete") else "available",
            "discovery uses demo orchestration; real data enriches outputs",
        ),
        "report": _entry("available"),
    }
    return matrix
