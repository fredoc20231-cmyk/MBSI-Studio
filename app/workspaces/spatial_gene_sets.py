"""Spatial Gene Sets workspace."""

from __future__ import annotations

import streamlit as st

from app.workspaces._helpers import safe_register_table
from app.workspaces._spatial_page import render_continue, render_page_header, require_adata
from mbsi.discovery.spatial_workflow_evidence import enrichment_to_evidence
from mbsi.enrichment import run_custom_enrichment, run_enrichment, run_spatial_gsea


def _merge_session_findings(store) -> None:
    session = store.to_session_dict()
    st.session_state.setdefault("findings", []).extend(session.get("findings", []))
    st.session_state.setdefault("evidence", []).extend(session.get("evidence", []))


def render() -> None:
    render_page_header(
        "Spatial Gene Sets",
        "Run enrichment and spatial GSEA on variable gene rankings.",
        icon="📚",
    )
    if not require_adata("spatial_gene_sets"):
        return

    library = st.selectbox(
        "Gene set library",
        ["hallmark", "go_bp", "reactome", "kegg", "custom", "spatial_gsea"],
        key="sgs_library",
    )
    svg = st.session_state.get("spatial_stats")
    if svg is not None and hasattr(svg, "head"):
        default_genes = svg.head(50)["gene"].tolist() if "gene" in svg.columns else []
    else:
        default_genes = list(st.session_state.adata.var_names[:30])

    genes_text = st.text_area("Gene list (comma-separated)", value=", ".join(default_genes), key="sgs_genes")
    genes = [g.strip() for g in genes_text.split(",") if g.strip()]

    if st.button("Run enrichment", type="primary", key="sgs_run"):
        if library == "spatial_gsea" and svg is not None:
            result = run_spatial_gsea(svg, library="hallmark")
        elif library == "custom":
            custom = {"immune": ["CD3D", "CD8A", "CD68"], "stromal": ["COL1A1", "ACTA2"]}
            result = run_custom_enrichment(genes, custom)
        else:
            result = run_enrichment(genes, library=library)
        st.session_state.run_outputs["spatial_gene_sets"] = {"enrichment": result.to_dict()}
        safe_register_table("spatial_gene_sets", f"enrichment_{library}", result)
        store, warnings = enrichment_to_evidence(result, library, readiness=st.session_state.get("mbsi_readiness"))
        _merge_session_findings(store)
        for w in warnings:
            st.warning(w)
        st.dataframe(result, use_container_width=True)

    render_continue("spatial_gene_sets")
