"""TME analysis pipeline orchestrator."""

from __future__ import annotations

from typing import Any, Dict, Optional

import anndata as ad
import pandas as pd

from mbsi.tme.immune_exclusion import detect_immune_exclusion, immune_exclusion_table
from mbsi.tme.tls import detect_tls_niches, tls_table
from mbsi.tme.caf_barriers import detect_caf_barriers, caf_barrier_table
from mbsi.tme.angiogenesis import score_angiogenic_regions, angiogenesis_table
from mbsi.tme.hypoxia import score_hypoxic_niches, hypoxia_table
from mbsi.tme.invasion import detect_invasive_fronts, invasion_table
from mbsi.tme.demo import make_tme_demo_adata

TME_GUARDRAIL = (
    "Analytical outputs are computational results for research use only. "
    "Biological and clinical conclusions require independent validation."
)


def run_tme_analysis(
    adata: Optional[ad.AnnData] = None,
    layer: str = "logcounts",
    seed: int = 42,
) -> Dict[str, Any]:
    """Run full tumor microenvironment niche detection pipeline."""
    if adata is None:
        adata = make_tme_demo_adata(seed=seed)

    immune_ex = detect_immune_exclusion(adata, layer=layer)
    tls = detect_tls_niches(adata, layer=layer)
    caf = detect_caf_barriers(adata, layer=layer)
    angio = score_angiogenic_regions(adata, layer=layer)
    hypoxia = score_hypoxic_niches(adata, layer=layer)
    invasion = detect_invasive_fronts(adata, layer=layer)

    niches = {
        "immune_exclusion": immune_ex,
        "tls_like": tls,
        "caf_barriers": caf,
        "hypoxic": hypoxia,
        "angiogenic": angio,
        "invasive_fronts": invasion,
    }

    summary_rows = []
    for key, res in niches.items():
        summary_rows.append({
            "niche_type": res["label"],
            "key": key,
            "n_spots_detected": res["n_niches"],
            "mean_score": res["mean_score"],
            "hypothesis": res["hypothesis"],
        })
    summary = pd.DataFrame(summary_rows)

    scores = pd.DataFrame({"spot": adata.obs_names})
    for key, res in niches.items():
        scores[f"{key}_score"] = res["score"]
        scores[f"{key}_detected"] = res["mask"]

    biomarkers = _rank_biomarker_candidates(adata, niches, layer=layer)

    from mbsi.tme.scores import score_marker_programs, program_summary
    program_scores = score_marker_programs(adata, layer=layer)
    program_summary_df = program_summary(program_scores)

    return {
        "adata": adata,
        "niches": niches,
        "summary": summary,
        "scores": scores,
        "biomarkers": biomarkers,
        "program_scores": program_scores,
        "program_summary": program_summary_df,
        "guardrail": TME_GUARDRAIL,
        "tables": {
            "immune_exclusion": immune_exclusion_table(adata, immune_ex),
            "tls": tls_table(adata, tls),
            "caf_barriers": caf_barrier_table(adata, caf),
            "angiogenesis": angiogenesis_table(adata, angio),
            "hypoxia": hypoxia_table(adata, hypoxia),
            "invasion": invasion_table(adata, invasion),
        },
    }


def _rank_biomarker_candidates(adata, niches, layer: str) -> pd.DataFrame:
    """Rank genes correlating with niche scores."""
    from mbsi.tme._utils import get_expression
    import numpy as np

    rows = []
    biomarker_genes = [
        "CD8A", "PDCD1", "CD274", "CXCL13", "ACTA2", "FAP",
        "VEGFA", "HIF1A", "CA9", "EPCAM", "MKI67",
    ]
    for key, res in niches.items():
        score = res["score"]
        for gene in biomarker_genes:
            if gene not in adata.var_names:
                continue
            expr = get_expression(adata, [gene], layer)
            if score.std() > 0 and expr.std() > 0:
                corr = float(np.corrcoef(score, expr)[0, 1])
            else:
                corr = 0.0
            rows.append({
                "niche": key,
                "gene": gene,
                "correlation": corr,
                "candidate_score": abs(corr),
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("candidate_score", ascending=False).reset_index(drop=True)
    return df


def export_tme_results(results: Dict[str, Any], out_dir) -> None:
    """Export TME CSVs."""
    from pathlib import Path

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results["summary"].to_csv(out_dir / "tme_niches.csv", index=False)
    results["scores"].to_csv(out_dir / "tme_scores.csv", index=False)
    results["biomarkers"].to_csv(out_dir / "tme_biomarkers.csv", index=False)
