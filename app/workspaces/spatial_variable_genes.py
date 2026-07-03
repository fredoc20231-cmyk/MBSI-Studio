"""Spatial Variable Genes workspace."""

from __future__ import annotations

import streamlit as st

from app.workspaces._helpers import safe_register_table
from app.workspaces._spatial_page import render_continue, render_page_header, require_adata
from mbsi.discovery.spatial_workflow_evidence import svg_to_evidence
from mbsi.spatial_stats import detect_svgs, spatial_autocorrelation_table


def _merge_session_findings(store) -> None:
    session = store.to_session_dict()
    st.session_state.setdefault("findings", []).extend(session.get("findings", []))
    st.session_state.setdefault("evidence", []).extend(session.get("evidence", []))


def render() -> None:
    render_page_header(
        "Spatial Variable Genes",
        "Detect spatially variable genes with Moran's I / Geary's C and "
        "permutation-tested significance (Benjamini-Hochberg FDR).",
        icon="🧬",
    )
    if not require_adata("spatial_variable_genes"):
        return

    adata = st.session_state.adata
    n_top = st.slider("Top genes to test", 100, 3000, 500, key="svg_n_top")
    k = st.slider("kNN neighbors", 4, 20, 6, key="svg_k")
    rigorous = st.checkbox(
        "Significance testing (p-values + FDR)",
        value=True,
        key="svg_rigorous",
        help="Run detect_svgs: analytic (Cliff-Ord) or permutation p-values with "
        "Benjamini-Hochberg FDR and an is_svg call. Uncheck for legacy point "
        "estimates only.",
    )
    method = "moran"
    n_perms = 0
    fdr_alpha = 0.05
    if rigorous:
        c1, c2, c3 = st.columns(3)
        method = c1.selectbox("Statistic", ["moran", "geary"], key="svg_method")
        n_perms = c2.slider(
            "Permutations (0 = analytic, Moran only)", 0, 999, 0, step=100,
            key="svg_nperms",
            help="0 uses the fast Cliff-Ord analytic null (Moran only); "
            ">0 uses a permutation null (required for Geary).",
        )
        fdr_alpha = c3.number_input(
            "FDR alpha", 0.001, 0.25, 0.05, step=0.01, key="svg_fdr"
        )

    if st.button("Run SVG analysis", type="primary", key="svg_run"):
        if rigorous:
            table = detect_svgs(
                adata,
                n_top=n_top,
                k=k,
                method=method,
                n_perms=int(n_perms),
                fdr_alpha=float(fdr_alpha),
            )
        else:
            table = spatial_autocorrelation_table(adata, n_top=n_top, k=k)
        st.session_state.spatial_stats = table
        st.session_state.run_outputs["spatial_variable_genes"] = {"svg_table": table.to_dict()}
        safe_register_table("spatial_variable_genes", "svg_rankings", table)
        readiness = st.session_state.get("mbsi_readiness")
        store, warnings = svg_to_evidence(table, readiness=readiness, run_id=st.session_state.get("last_run", ""))
        _merge_session_findings(store)
        for w in warnings:
            st.warning(w)
        if "is_svg" in table.columns:
            n_sig = int(table["is_svg"].sum())
            st.success(
                f"Computed SVG for {len(table)} genes — "
                f"{n_sig} significant at FDR < {fdr_alpha:g}."
            )
        else:
            st.success(f"Computed SVG for {len(table)} genes.")

    if st.session_state.get("spatial_stats") is not None:
        st.dataframe(st.session_state.spatial_stats.head(30), use_container_width=True)

    render_continue("spatial_variable_genes")
