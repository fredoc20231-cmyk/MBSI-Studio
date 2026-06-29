"""Ultra-high-resolution discovery functions for STOmics Stereo-seq."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import anndata as ad
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors

from mbsi.analysis.spatial_stats import build_spatial_weights, morans_i
from mbsi.discovery_model.entities import Finding
from mbsi.discovery_model.evidence import create_evidence
from mbsi.discovery_model.ontology import FindingType


def _platform_ok(adata: ad.AnnData, platform: Optional[str]) -> bool:
    plat = platform or adata.uns.get("mbsi_platform", "")
    if plat == "stereo_seq":
        return True
    from mbsi.schema.technology import TECHNOLOGIES

    spec = TECHNOLOGIES.get(plat, {})
    return spec.get("resolution_class") == "ultra_high"


def _require_ultra_high(adata: ad.AnnData, platform: Optional[str]) -> None:
    if not _platform_ok(adata, platform):
        raise ValueError("Discovery functions require stereo_seq or ultra_high resolution platform")


def identify_micro_niches(
    adata: ad.AnnData,
    *,
    platform: Optional[str] = None,
    k: int = 6,
    n_niches: int = 5,
) -> List[Finding]:
    """Detect micro-niches via local kNN composition clustering."""
    _require_ultra_high(adata, platform)
    coords = np.asarray(adata.obsm["spatial"])
    n = adata.n_obs
    k_use = min(k, n - 1)
    nn = NearestNeighbors(n_neighbors=k_use).fit(coords)
    _, idx = nn.kneighbors(coords)

    if "cluster" in adata.obs:
        labels = adata.obs["cluster"].astype(str).values
        uniq = sorted(set(labels))
        comp = np.zeros((n, len(uniq)))
        for i, u in enumerate(uniq):
            comp[:, i] = (labels == u).astype(float)
    else:
        X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
        comp = X[:, : min(20, X.shape[1])]

    local = np.array([comp[i].mean(axis=0) for i in idx])
    n_niches = min(n_niches, max(2, n // 20))
    km = KMeans(n_clusters=n_niches, random_state=42, n_init=10)
    niche_ids = km.fit_predict(local)

    findings: List[Finding] = []
    for nid in range(n_niches):
        count = int((niche_ids == nid).sum())
        if count < 3:
            continue
        ev = create_evidence(
            "discovery", "niche", f"Micro-niche {nid}",
            description=f"{count} bins in ultra-local neighborhood cluster",
            value=count,
        )
        findings.append(
            Finding.create(
                title=f"Micro-niche {nid}",
                summary=f"Ultra-local niche comprising {count} bins/cells at Stereo-seq resolution",
                finding_type=FindingType.NICHE.value,
                module="discovery",
                evidence_ids=[ev.evidence_id],
                metadata={"niche_id": nid, "n_bins": count, "platform": "stereo_seq"},
                platform="stereo_seq",
            )
        )
    return findings


def identify_transition_boundaries(
    adata: ad.AnnData,
    *,
    platform: Optional[str] = None,
    k: int = 8,
) -> List[Finding]:
    """Find transition boundaries where local composition changes sharply."""
    _require_ultra_high(adata, platform)
    coords = np.asarray(adata.obsm["spatial"])
    n = adata.n_obs
    nn = NearestNeighbors(n_neighbors=min(k, n)).fit(coords)
    _, idx = nn.kneighbors(coords)

    if "cluster" in adata.obs:
        labels = adata.obs["cluster"].astype(str).values
    elif "region_id" in adata.obs:
        labels = adata.obs["region_id"].astype(str).values
    else:
        X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
        labels = KMeans(n_clusters=min(5, max(2, n // 50)), random_state=0, n_init=10).fit_predict(X[:, :10]).astype(str)

    boundary_scores = []
    for i in range(n):
        neigh = labels[idx[i]]
        boundary_scores.append(len(set(neigh)) / len(neigh))

    scores = np.array(boundary_scores)
    threshold = np.quantile(scores, 0.9)
    boundary_idx = np.where(scores >= threshold)[0]
    findings: List[Finding] = []
    if len(boundary_idx) == 0:
        return findings

    ev = create_evidence(
        "discovery", "metric", "Transition boundary score",
        description=f"{len(boundary_idx)} high-transition loci",
        value=float(scores.max()),
    )
    findings.append(
        Finding.create(
            title="Spatial transition boundaries",
            summary=f"Detected {len(boundary_idx)} ultra-local transition loci between niches/clusters",
            finding_type=FindingType.NICHE.value,
            module="discovery",
            evidence_ids=[ev.evidence_id],
            metadata={"n_boundary_bins": len(boundary_idx), "max_score": float(scores.max())},
            platform="stereo_seq",
        )
    )
    return findings


def identify_spatial_gradients(
    adata: ad.AnnData,
    genes: Optional[List[str]] = None,
    *,
    platform: Optional[str] = None,
) -> List[Finding]:
    """Identify genes with strong spatial gradients (Moran's I + axis correlation)."""
    _require_ultra_high(adata, platform)
    coords = np.asarray(adata.obsm["spatial"])
    if genes is None:
        X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
        var = np.var(X, axis=0)
        top = np.argsort(var)[-min(10, adata.n_vars) :][::-1]
        genes = [adata.var_names[i] for i in top]

    morans_df = morans_i(adata, [g for g in genes if g in adata.var_names], k=6, layer="")
    findings: List[Finding] = []
    for _, row in morans_df.head(5).iterrows():
        gene = row["gene"]
        x = adata[:, gene].X
        expr = np.asarray(x).flatten() if not hasattr(x, "toarray") else x.toarray().flatten()
        gx = np.corrcoef(coords[:, 0], expr)[0, 1]
        gy = np.corrcoef(coords[:, 1], expr)[0, 1]
        gradient_strength = max(abs(gx), abs(gy))
        ev = create_evidence(
            "discovery", "metric", f"Gradient: {gene}",
            value=float(gradient_strength),
            description=f"Moran's I={row['morans_i']:.3f}",
        )
        findings.append(
            Finding.create(
                title=f"Spatial gradient: {gene}",
                summary=f"{gene} shows ultra-local spatial gradient (Moran's I={row['morans_i']:.3f})",
                finding_type=FindingType.BIOMARKER.value,
                module="discovery",
                evidence_ids=[ev.evidence_id],
                metadata={"gene": gene, "morans_i": float(row["morans_i"])},
                platform="stereo_seq",
            )
        )
    return findings


def identify_ultra_local_signaling(
    adata: ad.AnnData,
    ligand_genes: Optional[List[str]] = None,
    *,
    platform: Optional[str] = None,
    k: int = 5,
) -> List[Finding]:
    """Detect ultra-local L-R co-expression pockets."""
    _require_ultra_high(adata, platform)
    if ligand_genes is None:
        ligand_genes = [g for g in ("CXCL12", "TGFB1", "VEGFA", "IL6", "CCL2") if g in adata.var_names]
    if len(ligand_genes) < 1:
        return []

    coords = np.asarray(adata.obsm["spatial"])
    nn = NearestNeighbors(n_neighbors=min(k, adata.n_obs)).fit(coords)
    _, idx = nn.kneighbors(coords)
    findings: List[Finding] = []

    for gene in ligand_genes[:5]:
        x = adata[:, gene].X
        expr = np.asarray(x).flatten() if not hasattr(x, "toarray") else x.toarray().flatten()
        local_mean = np.array([expr[i].mean() for i in idx])
        hotspots = (local_mean > np.quantile(local_mean, 0.95)).sum()
        if hotspots < 2:
            continue
        ev = create_evidence(
            "discovery", "pathway", f"Ultra-local signaling: {gene}",
            value=int(hotspots),
            description=f"{hotspots} signaling hotspots",
        )
        findings.append(
            Finding.create(
                title=f"Ultra-local signaling: {gene}",
                summary=f"{gene} enriched in {hotspots} ultra-local signaling hotspots",
                finding_type=FindingType.LR_PATHWAY.value,
                module="discovery",
                evidence_ids=[ev.evidence_id],
                metadata={"ligand": gene, "n_hotspots": int(hotspots)},
                platform="stereo_seq",
            )
        )
    return findings


def identify_ultra_resolution_biomarkers(
    adata: ad.AnnData,
    *,
    platform: Optional[str] = None,
    top_n: int = 5,
) -> List[Finding]:
    """Flag biomarkers with high spatial variance at ultra-high resolution."""
    _require_ultra_high(adata, platform)
    X = adata.X.toarray() if hasattr(adata.X, "toarray") else np.asarray(adata.X)
    spatial_var = np.var(X, axis=0)
    top_idx = np.argsort(spatial_var)[-top_n:][::-1]
    findings: List[Finding] = []
    for i in top_idx:
        gene = adata.var_names[i]
        ev = create_evidence(
            "discovery", "metric", f"Ultra-resolution biomarker: {gene}",
            value=float(spatial_var[i]),
        )
        findings.append(
            Finding.create(
                title=f"Ultra-resolution biomarker: {gene}",
                summary=f"{gene} exhibits high spatial variance consistent with Stereo-seq resolution",
                finding_type=FindingType.BIOMARKER.value,
                module="discovery",
                evidence_ids=[ev.evidence_id],
                metadata={"gene": gene, "spatial_variance": float(spatial_var[i])},
                platform="stereo_seq",
            )
        )
    return findings


def run_stereo_seq_discovery(
    adata: ad.AnnData,
    platform: Optional[str] = None,
) -> Dict[str, Any]:
    """Run all Stereo-seq discovery functions and return findings list."""
    all_findings: List[Finding] = []
    for fn in (
        identify_micro_niches,
        identify_transition_boundaries,
        identify_spatial_gradients,
        identify_ultra_local_signaling,
        identify_ultra_resolution_biomarkers,
    ):
        try:
            all_findings.extend(fn(adata, platform=platform))
        except ValueError:
            pass
    return {"findings": all_findings, "n_findings": len(all_findings)}
