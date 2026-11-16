"""Visium capability core: Biomni-style spatial workflow with provenance guardrails.

Every module returns observed outputs only. When inputs, replicates or
libraries are missing the module returns a ``blocked`` state, never a substitute.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from .cci import cell_interactions
from .deconvolution import deconvolve
from .niches import spatial_niches
from .provenance import BlockedAnalysis, blocked, package_versions, provenance
from .replicate_de import replicate_aware_de
from .spatial import neighborhood_statistics, spatially_variable_genes
from .visium_hd import visium_hd_bin

_MODULES: Dict[str, Dict[str, Any]] = {
    "visium_svg": {"phase": 1, "label": "Spatially variable genes (Moran's I, BH-FDR)", "fn": spatially_variable_genes, "packages": ["squidpy"], "tier": "statistically_supported"},
    "visium_neighborhood": {"phase": 1, "label": "Neighborhood enrichment, co-occurrence, Ripley, interaction matrix", "fn": neighborhood_statistics, "packages": ["squidpy"], "tier": "statistically_supported"},
    "visium_niches": {"phase": 2, "label": "Spatially-aware domains and niches", "fn": spatial_niches, "packages": ["scanpy", "squidpy"], "tier": "observed"},
    "visium_deconvolution": {"phase": 3, "label": "Spot deconvolution", "fn": deconvolve, "packages": ["tangram-sc", "cell2location"], "tier": "observed"},
    "visium_replicate_de": {"phase": 4, "label": "Replicate-aware pseudobulk DE", "fn": replicate_aware_de, "packages": ["pydeseq2"], "tier": "statistically_supported"},
    "visium_cci": {"phase": 5, "label": "Cell-cell interaction (hypothesis-level)", "fn": cell_interactions, "packages": ["squidpy", "omnipath"], "tier": "hypothesis"},
    "visium_hd_bin": {"phase": 7, "label": "Visium HD binning and QC", "fn": visium_hd_bin, "packages": ["scipy"], "tier": "observed"},
}

MODULE_NAMES = tuple(_MODULES)


def capabilities() -> List[Dict[str, Any]]:
    out = []
    for name, spec in _MODULES.items():
        versions = package_versions(spec["packages"])
        out.append({
            "module": name,
            "phase": spec["phase"],
            "label": spec["label"],
            "evidence_tier": spec["tier"],
            "packages": versions,
            "installed": any(v is not None for v in versions.values()) if name == "visium_deconvolution" else all(v is not None for v in versions.values()),
        })
    return out


def run_visium_module(module: str, adata, params: Dict[str, Any]) -> Dict[str, Any]:
    spec = _MODULES[module]
    fn: Callable[..., Dict[str, Any]] = spec["fn"]
    if adata is None:
        return blocked(module, BlockedAnalysis("No observed dataset loaded.", "Upload a dataset first."), params)
    try:
        outputs = fn(adata, params)
    except BlockedAnalysis as exc:
        return blocked(module, exc, params)
    return {"status": "complete", "module": module, "outputs": outputs, "provenance": provenance(module, fn, params, spec["packages"], spec["tier"])}
