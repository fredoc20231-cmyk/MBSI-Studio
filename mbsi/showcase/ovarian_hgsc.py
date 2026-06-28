"""Ovarian HGSOC flagship showcase — synthetic spatial demo."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.communication import run_communication_analysis
from mbsi.tme import run_tme_analysis, detect_immune_exclusion, detect_caf_barriers

SHOWCASE_GUARDRAIL = (
    "Analytical outputs are computational results for research use only. "
    "All HGSOC findings are computational hypotheses requiring independent validation."
)

HGSOC_CELL_TYPES = [
    "Tumor Epithelial",
    "CAF",
    "T cells",
    "Macrophages",
    "Endothelial",
]

HGSOC_GENES = [
    "EPCAM", "KRT8", "MKI67", "CXCL12", "CXCR4",
    "ACTA2", "FAP", "COL1A1", "CD8A", "CD3D", "MS4A1",
    "CD68", "PECAM1", "VEGFA", "HIF1A", "CA9",
    "ABCB1", "ABCC2", "ERCC1", "MCL1", "BRCA1", "BRCA2", "PARP1", "GSTP1", "RAD51", "ATM",
    "TGFB1", "CD274", "PDCD1",
]

PLATINUM_RESISTANCE_GENES = ["ABCB1", "ABCC2", "ERCC1", "MCL1", "GSTP1"]
PARP_RESISTANCE_GENES = ["BRCA1", "BRCA2", "PARP1", "RAD51", "ATM"]


def make_ovarian_showcase_adata(n_spots: int = 120, seed: int = 42) -> ad.AnnData:
    """Synthetic but biologically plausible HGSOC Visium-like spatial data."""
    rng = np.random.default_rng(seed)
    side = int(np.ceil(np.sqrt(n_spots)))
    rows, cols = np.divmod(np.arange(n_spots), side)
    coords = np.column_stack([
        cols * 12 + rng.normal(0, 0.6, n_spots),
        rows * 12 + rng.normal(0, 0.6, n_spots),
    ])

    # Spatial niches: tumor core, CAF barrier ring, immune desert, CXCL12 gradient axis
    cxcl12_axis = np.exp(-((coords[:, 0] - coords[:, 0].mean()) ** 2) / (2 * 40 ** 2))
    tumor_core = np.sqrt((coords[:, 0] - coords[:, 0].max() * 0.65) ** 2 +
                         (coords[:, 1] - coords[:, 1].mean()) ** 2) < 35
    caf_ring = (~tumor_core) & (np.sqrt(
        (coords[:, 0] - coords[:, 0].max() * 0.65) ** 2 +
        (coords[:, 1] - coords[:, 1].mean()) ** 2
    ) < 55)

    types = np.array(["Tumor Epithelial"] * n_spots, dtype=object)
    types[caf_ring] = "CAF"
    for i in range(n_spots):
        if types[i] != "CAF" and not tumor_core[i]:
            r = rng.random()
            if r < 0.08:
                types[i] = "T cells"
            elif r < 0.12:
                types[i] = "Macrophages"
            elif r < 0.14:
                types[i] = "Endothelial"

    extra = [f"GENE{i}" for i in range(15)]
    all_genes = HGSOC_GENES + [g for g in extra if g not in HGSOC_GENES]
    X = np.zeros((n_spots, len(all_genes)), dtype=np.float32)
    gene_idx = {g: i for i, g in enumerate(all_genes)}

    for i in range(n_spots):
        ct = types[i]
        base = rng.uniform(1, 3)
        for g in all_genes:
            lam = base
            if g in ("EPCAM", "KRT8", "MKI67") and ct == "Tumor Epithelial":
                lam = 4 * (1.5 if tumor_core[i] else 1.0)
            elif g in ("ACTA2", "FAP", "COL1A1") and (ct == "CAF" or caf_ring[i]):
                lam = 5
            elif g in ("CD8A", "CD3D") and ct == "T cells":
                lam = 4
            elif g == "CD68" and ct == "Macrophages":
                lam = 4
            elif g == "PECAM1" and ct == "Endothelial":
                lam = 3
            elif g == "CXCL12":
                lam = 3 + 4 * cxcl12_axis[i]
            elif g == "CXCR4" and tumor_core[i]:
                lam = 3
            elif g in PLATINUM_RESISTANCE_GENES and tumor_core[i]:
                lam = 2 + 3 * (1 if rng.random() > 0.5 else 0.5)
            elif g in PARP_RESISTANCE_GENES and tumor_core[i]:
                lam = 1.5 + 2 * rng.uniform(0.5, 1.5)
            X[i, gene_idx[g]] = rng.poisson(max(lam, 0.1))

    adata = ad.AnnData(X=X)
    adata.var_names = all_genes
    adata.obs_names = [f"HGSOC-{i:04d}" for i in range(n_spots)]
    adata.obsm["spatial"] = coords.astype(np.float32)
    adata.obs["cell_type"] = types
    adata.obs["in_tissue"] = np.ones(n_spots, dtype=bool)
    totals = X.sum(axis=1, keepdims=True) + 1e-12
    adata.layers["counts"] = X.copy()
    adata.layers["logcounts"] = np.log1p(X / totals * 1e4)
    adata.uns["platform"] = "synthetic_hgsc_visium"
    adata.uns["disease"] = "HGSOC"
    return adata


def _score_signature(adata: ad.AnnData, genes: List[str], layer: str = "logcounts") -> np.ndarray:
    present = [g for g in genes if g in adata.var_names]
    if not present:
        return np.zeros(adata.n_obs)
    if layer in adata.layers:
        X = adata[:, present].layers[layer]
    else:
        X = adata[:, present].X
    X = np.asarray(X.toarray() if hasattr(X, "toarray") else X, dtype=float)
    return X.mean(axis=1)


def score_resistance_programs(adata: ad.AnnData, layer: str = "logcounts") -> pd.DataFrame:
    """Score cisplatin and PARP resistance programs from gene signatures."""
    plat = _score_signature(adata, PLATINUM_RESISTANCE_GENES + ["GSTP1"], layer)
    parp = _score_signature(adata, PARP_RESISTANCE_GENES, layer)
    coords = adata.obsm["spatial"]
    return pd.DataFrame({
        "spot": adata.obs_names,
        "platinum_resistance_score": plat,
        "parp_resistance_score": parp,
        "combined_resistance": (plat + parp) / 2,
        "x": coords[:, 0],
        "y": coords[:, 1],
    })


def run_ovarian_showcase_pipeline(
    adata: Optional[ad.AnnData] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """Full HGSOC showcase integrating spatial, communication, TME, and resistance."""
    if adata is None:
        adata = make_ovarian_showcase_adata(seed=seed)

    communication = run_communication_analysis(adata, k=6)
    tme = run_tme_analysis(adata)
    resistance = score_resistance_programs(adata)

    immune_ex = tme["niches"]["immune_exclusion"]
    caf = tme["niches"]["caf_barriers"]
    cxcl12_rank = communication["pathway_rankings"]
    cxcl12_row = cxcl12_rank[cxcl12_rank["pathway_name"].str.contains("CXCL12", na=False)]
    cxcl12_score = float(cxcl12_row.iloc[0]["score"]) if not cxcl12_row.empty else 0.0

    plat_threshold = np.percentile(resistance["platinum_resistance_score"], 75)
    plat_mask = resistance["platinum_resistance_score"] >= plat_threshold

    findings = {
        "caf_barrier_niches": {
            "n_spots": int(caf["n_niches"]),
            "mean_score": float(caf["mean_score"]),
            "label": "CAF barrier niches detected at tumor-stroma interface",
            "hypothesis": "computational_hypothesis",
        },
        "cxcl12_signaling_regions": {
            "top_pathway_score": cxcl12_score,
            "top_pathway": "CXCL12-CXCR4",
            "label": "CXCL12-CXCR4 signaling enriched in spatial gradient regions",
            "hypothesis": "computational_hypothesis",
        },
        "immune_excluded_tumor_fronts": {
            "n_spots": int(immune_ex["n_niches"]),
            "mean_score": float(immune_ex["mean_score"]),
            "label": "Immune-excluded tumor fronts with low T-cell infiltration",
            "hypothesis": "computational_hypothesis",
        },
        "platinum_resistance_microenvironments": {
            "n_spots": int(plat_mask.sum()),
            "mean_score": float(resistance.loc[plat_mask, "platinum_resistance_score"].mean()) if plat_mask.any() else 0.0,
            "label": "Platinum-resistance gene signature enriched in tumor core niches",
            "hypothesis": "computational_hypothesis",
        },
    }

    biomarkers = tme["biomarkers"].copy()
    biomarkers["showcase_context"] = "HGSOC"
    resistance_biomarkers = resistance.nlargest(10, "combined_resistance")[
        ["spot", "platinum_resistance_score", "parp_resistance_score", "combined_resistance"]
    ]

    try:
        from app.components.demo_data import _generate_he_image
        histology = _generate_he_image(seed=seed)
    except Exception:
        histology = None

    return {
        "adata": adata,
        "communication": communication,
        "tme": tme,
        "resistance": resistance,
        "findings": findings,
        "biomarkers": biomarkers,
        "resistance_biomarkers": resistance_biomarkers,
        "histology_image": histology,
        "guardrail": SHOWCASE_GUARDRAIL,
        "seed": seed,
        "disease": "High-Grade Serous Ovarian Cancer (HGSOC)",
    }


def export_ovarian_showcase(results: Dict[str, Any], out_dir) -> None:
    """Export showcase CSV/JSON outputs."""
    import json
    from pathlib import Path

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results["biomarkers"].to_csv(out_dir / "ovarian_showcase_biomarkers.csv", index=False)
    summary = {
        "disease": results["disease"],
        "seed": results["seed"],
        "findings": results["findings"],
        "guardrail": results["guardrail"],
        "top_communication_pathway": results["communication"].get("top_pathway"),
    }
    (out_dir / "ovarian_showcase_summary.json").write_text(json.dumps(summary, indent=2, default=str))
