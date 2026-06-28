"""Ligand-receptor pair scoring and communication pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import anndata as ad
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from mbsi.communication._utils import get_expression, resolve_gene
from mbsi.communication.diffusion_flux import compute_diffusion_flux
from mbsi.communication.sender_receiver import rank_sender_receiver
from mbsi.communication.niche_maps import build_niche_interaction_map

COMMUNICATION_GUARDRAIL = (
    "Communication scores are computational hypotheses for research use only. "
    "Pathway activity requires independent experimental validation."
)

DEFAULT_PATHWAYS: List[Dict[str, str]] = [
    {"pathway": "CXCL12-CXCR4", "ligand": "CXCL12", "receptor": "CXCR4"},
    {"pathway": "TGFB1-TGFBR", "ligand": "TGFB1", "receptor": "TGFBR1"},
    {"pathway": "PD-L1-PD1", "ligand": "CD274", "receptor": "PDCD1"},
    {"pathway": "VEGFA-VEGFR2", "ligand": "VEGFA", "receptor": "KDR"},
    {"pathway": "MIF-CD74", "ligand": "MIF", "receptor": "CD74"},
]

GENE_ALIASES: Dict[str, List[str]] = {
    "CXCR4": ["CXCR4"],
    "TGFBR1": ["TGFBR1", "TGFBR2", "TGFBR"],
    "PD-L1": ["CD274", "PDL1"],
    "PD1": ["PDCD1", "PD1"],
    "VEGFR2": ["KDR", "VEGFR2", "FLK1"],
}


def _resolve_gene(adata: ad.AnnData, gene: str) -> Optional[str]:
    return resolve_gene(adata, gene)


def _expression(adata: ad.AnnData, gene: str, layer: str = "logcounts") -> np.ndarray:
    return get_expression(adata, gene, layer)

def make_communication_demo_adata(n_spots: int = 80, seed: int = 42) -> ad.AnnData:
    """Synthetic AnnData with pathway genes and spatial expression gradients."""
    rng = np.random.default_rng(seed)
    from mbsi.analysis.demo import make_synthetic_visium_adata

    adata = make_synthetic_visium_adata(n_spots=n_spots, n_genes=50, seed=seed)
    pathway_genes = list({p["ligand"] for p in DEFAULT_PATHWAYS} | {p["receptor"] for p in DEFAULT_PATHWAYS})
    extra = [f"GENE{i}" for i in range(max(0, 60 - len(pathway_genes)))]
    all_genes = pathway_genes + extra

    coords = adata.obsm["spatial"]
    n = adata.n_obs
    X = np.zeros((n, len(all_genes)), dtype=np.float32)
    for j, gene in enumerate(all_genes):
        grad = 1.0 + 0.8 * np.sin(coords[:, 0] / 25 + j * 0.3)
        X[:, j] = rng.poisson(grad * rng.uniform(1, 4)).astype(np.float32)

    out = ad.AnnData(X=X)
    out.var_names = all_genes
    out.obs_names = adata.obs_names
    out.obsm["spatial"] = coords
    out.obs["in_tissue"] = np.ones(n, dtype=bool)
    totals = X.sum(axis=1, keepdims=True) + 1e-12
    logc = np.log1p(X / totals * 1e4)
    out.layers["counts"] = X.copy()
    out.layers["logcounts"] = logc
    return out


def score_ligand_receptor_pairs(
    adata: ad.AnnData,
    pairs: Optional[List[Tuple[str, str]]] = None,
    layer: str = "logcounts",
    k: int = 6,
) -> pd.DataFrame:
    """Score L-R pairs using expression product and spatial proximity."""
    if pairs is None:
        pairs = [(p["ligand"], p["receptor"]) for p in DEFAULT_PATHWAYS]

    coords = adata.obsm["spatial"]
    nn = NearestNeighbors(n_neighbors=min(k + 1, adata.n_obs)).fit(coords)
    dists, indices = nn.kneighbors(coords)

    rows = []
    for lig, rec in pairs:
        lig_g = _resolve_gene(adata, lig)
        rec_g = _resolve_gene(adata, rec)
        if lig_g is None or rec_g is None:
            rows.append({
                "ligand": lig, "receptor": rec, "pathway": f"{lig}-{rec}",
                "score": 0.0, "probability": 0.0, "status": "missing_genes",
            })
            continue

        lig_e = _expression(adata, lig, layer)
        rec_e = _expression(adata, rec, layer)
        pair_scores = []
        for i in range(adata.n_obs):
            for j_idx, j in enumerate(indices[i]):
                if i == j:
                    continue
                w = np.exp(-dists[i, j_idx] ** 2 / (2 * 30.0 ** 2))
                pair_scores.append(lig_e[i] * rec_e[j] * w)

        score = float(np.mean(pair_scores)) if pair_scores else 0.0
        prob = float(1.0 / (1.0 + np.exp(-score))) if score != 0 else 0.0
        rows.append({
            "ligand": lig_g,
            "receptor": rec_g,
            "pathway": f"{lig}-{rec}",
            "score": score,
            "probability": prob,
            "ligand_mean": float(lig_e.mean()),
            "receptor_mean": float(rec_e.mean()),
            "status": "ok",
        })
    df = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
    return df


def pathway_rankings(adata: ad.AnnData, layer: str = "logcounts") -> pd.DataFrame:
    """Rank canonical pathways by L-R communication score."""
    df = score_ligand_receptor_pairs(adata, layer=layer)
    name_map = {f"{p['ligand']}-{p['receptor']}": p["pathway"] for p in DEFAULT_PATHWAYS}
    df["pathway_name"] = df["pathway"].map(name_map).fillna(df["pathway"])
    return df.sort_values("score", ascending=False).reset_index(drop=True)


def run_communication_analysis(
    adata: ad.AnnData,
    layer: str = "logcounts",
    k: int = 6,
) -> Dict[str, Any]:
    """Full communication intelligence pipeline."""
    pair_scores = score_ligand_receptor_pairs(adata, layer=layer, k=k)
    rankings = pathway_rankings(adata, layer=layer)

    top_pair = rankings.iloc[0] if not rankings.empty else None
    sender_receiver = pd.DataFrame()
    flux_field = None
    niche_map = None

    if top_pair is not None and top_pair.get("status") == "ok":
        lig, rec = top_pair["ligand"], top_pair["receptor"]
        sr = rank_sender_receiver(adata, (lig, rec), k=k, layer=layer)
        sender_receiver = sr["table"]
        edges = sr["edges"]
        flux_field = compute_diffusion_flux(adata, lig, rec, k=k, layer=layer)
        niche_map = build_niche_interaction_map(adata, (lig, rec), layer=layer)
    else:
        edges = pd.DataFrame()

    return {
        "pair_scores": pair_scores,
        "pathway_rankings": rankings,
        "sender_receiver": sender_receiver,
        "edges": edges,
        "flux_field": flux_field,
        "niche_map": niche_map,
        "top_pathway": top_pair["pathway_name"] if top_pair is not None else None,
        "guardrail": COMMUNICATION_GUARDRAIL,
        "hypothesis_label": "computational_hypothesis",
    }


def export_communication_results(results: Dict[str, Any], out_dir) -> None:
    """Write communication CSV exports."""
    from pathlib import Path

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results["pair_scores"].to_csv(out_dir / "communication_pairs.csv", index=False)
    results["pathway_rankings"].to_csv(out_dir / "pathway_rankings.csv", index=False)
    if isinstance(results.get("sender_receiver"), pd.DataFrame) and not results["sender_receiver"].empty:
        results["sender_receiver"].to_csv(out_dir / "sender_receiver.csv", index=False)
