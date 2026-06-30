"""Gene set enrichment — GO, Hallmark, spatial GSEA with honest gseapy fallback."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd


GENE_SET_LIBRARIES = {
    "go_bp": "GO_Biological_Process_2021",
    "hallmark": "MSigDB_Hallmark_2020",
    "reactome": "Reactome_2022",
    "kegg": "KEGG_2021_Human",
}


def _stub_enrichment(genes: List[str], library: str) -> pd.DataFrame:
    """Honest stub when gseapy unavailable."""
    return pd.DataFrame(
        [
            {
                "term": f"[stub] {library} enrichment unavailable",
                "library": library,
                "n_genes": len(genes),
                "pval": 1.0,
                "note": "Install gseapy for full enrichment (pip install gseapy)",
            }
        ]
    )


def run_enrichment(
    genes: List[str],
    library: str = "hallmark",
    organism: str = "Human",
) -> pd.DataFrame:
    """Run over-representation enrichment."""
    lib_name = GENE_SET_LIBRARIES.get(library, library)
    try:
        import gseapy as gp

        enr = gp.enrichr(gene_list=genes[:500], gene_sets=lib_name, organism=organism, outdir=None, no_plot=True)
        if enr is not None and hasattr(enr, "results") and enr.results is not None:
            return enr.results
    except Exception:
        pass
    return _stub_enrichment(genes, lib_name)


def run_spatial_gsea(
    ranked_genes: pd.DataFrame,
    library: str = "hallmark",
) -> pd.DataFrame:
    """Spatial GSEA on ranked gene list (gene, score columns)."""
    if ranked_genes.empty or "gene" not in ranked_genes.columns:
        return pd.DataFrame()
    score_col = "morans_i" if "morans_i" in ranked_genes.columns else ranked_genes.columns[-1]
    rnk = ranked_genes[["gene", score_col]].dropna()
    rnk = rnk.sort_values(score_col, ascending=False)
    try:
        import gseapy as gp

        lib_name = GENE_SET_LIBRARIES.get(library, library)
        pre_res = gp.prerank(rnk=rnk, gene_sets=lib_name, outdir=None, seed=42, no_plot=True)
        if pre_res is not None and hasattr(pre_res, "res2d"):
            return pre_res.res2d
    except Exception:
        pass
    genes = rnk["gene"].tolist()[:50]
    return _stub_enrichment(genes, f"spatial_gsea_{library}")


def run_custom_enrichment(genes: List[str], custom_sets: Dict[str, List[str]]) -> pd.DataFrame:
    """Manual hypergeometric-style overlap against custom gene sets."""
    rows = []
    gene_set = set(genes)
    for term, term_genes in custom_sets.items():
        overlap = gene_set & set(term_genes)
        rows.append({
            "term": term,
            "library": "custom",
            "overlap": len(overlap),
            "n_genes": len(genes),
            "genes": ", ".join(sorted(overlap)[:10]),
        })
    return pd.DataFrame(rows)
