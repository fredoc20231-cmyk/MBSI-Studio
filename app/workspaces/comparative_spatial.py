"""Interactive two-tissue H5AD comparison workspace (real data only).

This is an exploratory preview. It does not perform statistical inference or
claim universal vendor-format ingestion. Use Study & Data for vendor bundles.
"""
from __future__ import annotations

import json
import os
import tempfile

import anndata as ad
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from mbsi.comparative import compare_samples, spatial_coordinates
from mbsi.comparative.neighborhoods import neighborhood_matrix


@st.cache_data(show_spinner=False, max_entries=6)
def _read_h5ad(content: bytes):
    """Keep each uploaded dataset independent; do not persist clinical data."""
    with tempfile.NamedTemporaryFile(suffix=".h5ad", delete=False) as handle:
        handle.write(content)
        path = handle.name
    try:
        return ad.read_h5ad(path)
    finally:
        os.unlink(path)


def _annotation_columns(adata) -> list[str]:
    return [
        key for key in adata.obs.columns
        if (pd.api.types.is_categorical_dtype(adata.obs[key])
            or pd.api.types.is_object_dtype(adata.obs[key])
            or pd.api.types.is_string_dtype(adata.obs[key]))
        and adata.obs[key].nunique() <= 100
    ]


def _choose_annotation(adata, label):
    options = _annotation_columns(adata)
    if not options:
        st.error(f"{label} has no categorical cell type / cluster labels. Annotate the sample first.")
        return None
    priority = ["cell_type", "celltype", "cell_type_pred", "leiden", "cluster", "clusters"]
    default = next((p for p in priority if p in options), options[0])
    return st.selectbox(f"{label} annotation", options, index=options.index(default),
                        key=f"cmp_label_{label}")


def _spatial_plot(adata, label_key, title):
    coords = spatial_coordinates(adata)
    if coords is None:
        st.info(f"{title}: no valid obsm['spatial'] coordinates; spatial map unavailable.")
        return
    labels = adata.obs[label_key].astype("string").fillna("Unassigned").astype(str).to_numpy()
    if len(coords) > 100000:
        st.warning(f"{title}: showing first 100,000 units for interactive display.")
        coords, labels = coords[:100000], labels[:100000]
    frame = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "Population": labels})
    fig = px.scatter(frame, x="x", y="y", color="Population", title=title,
                     render_mode="webgl", opacity=0.8)
    fig.update_traces(marker={"size": 3})
    fig.update_yaxes(autorange="reversed", scaleanchor="x", scaleratio=1)
    fig.update_layout(height=450, margin=dict(l=15, r=15, t=45, b=15))
    st.plotly_chart(fig, use_container_width=True)


def _gene_spatial_plot(adata, gene, title):
    coords = spatial_coordinates(adata)
    if coords is None:
        st.info(f"{title}: spatial coordinates not available.")
        return
    if gene not in adata.var_names:
        st.warning(f"{gene} is missing from {title}")
        return
    matrix = adata[:, [gene]].X
    if hasattr(matrix, "toarray"):
        matrix = matrix.toarray()
    values = np.asarray(matrix).ravel()
    if len(coords) > 100000:
        coords, values = coords[:100000], values[:100000]
    frame = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "Expression": values})
    fig = px.scatter(frame, x="x", y="y", color="Expression",
                     color_continuous_scale="Viridis", title=f"{title}: {gene}",
                     render_mode="webgl")
    fig.update_traces(marker={"size": 3})
    fig.update_yaxes(autorange="reversed", scaleanchor="x", scaleratio=1)
    fig.update_layout(height=450, margin=dict(l=15, r=15, t=45, b=15))
    st.plotly_chart(fig, use_container_width=True)


def render():
    st.title("Comparative Spatial Omics")
    st.caption("Real H5AD input · side-by-side tissue maps · annotation and expression comparisons")
    st.info(
        "Exploratory preview: compare two previously annotated samples. "
        "This workspace uses H5AD uploads; vendor bundles should first be converted "
        "by the established ingestion workflows. No p-values, batch correction, "
        "deconvolution or automatic cross-sample cluster matching are claimed."
    )

    files = st.file_uploader("Upload two or more annotated H5AD datasets",
                             type=["h5ad"], accept_multiple_files=True,
                             key="cmp_h5ad_upload")
    if not files or len(files) < 2:
        st.warning("Upload at least two H5AD files to enable the comparison controls.")
        return

    keys = [f"{i+1}. {file.name}" for i, file in enumerate(files)]
    col_a, col_b = st.columns(2)
    with col_a:
        key_a = st.selectbox("Reference tissue", keys, index=0, key="cmp_sample_a")
    with col_b:
        key_b = st.selectbox("Comparison tissue", keys, index=1, key="cmp_sample_b")
    if key_a == key_b:
        st.error("Choose different tissues.")
        return

    idx_a, idx_b = keys.index(key_a), keys.index(key_b)
    try:
        with st.spinner("Reading tissue datasets"):
            left = _read_h5ad(files[idx_a].getvalue())
            right = _read_h5ad(files[idx_b].getvalue())
    except Exception as exc:
        st.error(f"Unable to read one or both H5AD files: {exc}")
        return

    a1, b1, c1 = st.columns(3)
    a1.metric("Reference units", f"{left.n_obs:,}")
    b1.metric("Comparison units", f"{right.n_obs:,}")
    shared = sorted(set(map(str, left.var_names)) & set(map(str, right.var_names)))
    c1.metric("Shared genes", f"{len(shared):,}")
    if not shared:
        st.error("These datasets contain no common gene identifiers.")
        return

    left_col, right_col = st.columns(2)
    with left_col:
        label_a = _choose_annotation(left, "Reference")
    with right_col:
        label_b = _choose_annotation(right, "Comparison")
    if not label_a or not label_b:
        return

    st.caption("Shared labels denote matching annotation names, not independently verified cell-type correspondence.")
    genes = st.multiselect(
        "Genes to compare (select a panel; maximum 100)",
        shared, default=shared[:min(20, len(shared))],
        max_selections=100, key="cmp_genes"
    )
    if not genes:
        st.warning("Select at least one common gene.")
        return

    if st.button("Run descriptive tissue comparison", type="primary",
                 use_container_width=True, key="cmp_run"):
        try:
            result = compare_samples(
                left[:, genes].copy(), right[:, genes].copy(),
                left_id=key_a, right_id=key_b,
                left_label=label_a, right_label=label_b,
            )
            st.session_state["cmp_result"] = result
            st.session_state["cmp_config"] = (key_a, key_b, label_a, label_b, tuple(genes))
        except Exception as exc:
            st.error(f"Comparison failed: {exc}")
            return

    result = st.session_state.get("cmp_result")
    config = (key_a, key_b, label_a, label_b, tuple(genes))
    if result is None or st.session_state.get("cmp_config") != config:
        st.info("Choose your settings and run the comparison to display results.")
        return

    for warning in result["warnings"]:
        st.caption("⚠ " + warning)

    tabs = st.tabs(["Tissue maps", "Populations", "Gene expression", "Neighborhoods", "Export"])
    with tabs[0]:
        map_a, map_b = st.columns(2)
        with map_a:
            _spatial_plot(left, label_a, "Reference spatial map")
        with map_b:
            _spatial_plot(right, label_b, "Comparison spatial map")
        overlay_gene = st.selectbox("Gene expression overlay", genes, key="cmp_overlay_gene")
        g1, g2 = st.columns(2)
        with g1:
            _gene_spatial_plot(left, overlay_gene, "Reference")
        with g2:
            _gene_spatial_plot(right, overlay_gene, "Comparison")
    with tabs[1]:
        comp = result["composition"]
        st.dataframe(comp, use_container_width=True, hide_index=True)
        melted = comp.melt(id_vars="population", value_vars=["fraction_a", "fraction_b"],
                           var_name="Sample", value_name="Fraction")
        st.plotly_chart(px.bar(melted, x="population", y="Fraction", color="Sample",
                               barmode="group", title="Annotated population fractions"),
                        use_container_width=True)
    with tabs[2]:
        expr = result["expression"]
        if expr.empty:
            st.warning("No matching annotation labels between samples; expression matching is unavailable.")
        else:
            population = st.selectbox("Population", sorted(expr.population.unique()),
                                      key="cmp_population")
            subset = expr[expr.population == population]
            st.dataframe(subset, use_container_width=True, hide_index=True)
            chart = px.bar(subset.melt(id_vars="gene",
                            value_vars=["mean_expression_a", "mean_expression_b"],
                            var_name="Sample", value_name="Mean expression"),
                            x="gene", y="Mean expression", color="Sample", barmode="group")
            st.plotly_chart(chart, use_container_width=True)
            matrix = expr.pivot(index="population", columns="gene", values="delta_mean").fillna(0)
            if not matrix.empty:
                fig = px.imshow(matrix, aspect="auto",
                                title="Mean-expression difference (B minus A)",
                                color_continuous_scale="RdBu_r",
                                color_continuous_midpoint=0)
                st.plotly_chart(fig, use_container_width=True)
    with tabs[3]:
        st.caption("Observed neighborhood fractions, not statistical enrichment.")
        k = st.slider("Number of spatial neighbors", min_value=1, max_value=12,
                      value=6, key="cmp_neighborhood_k")
        n1, n2 = st.columns(2)
        for panel, adata, ann, title in (
            (n1, left, label_a, "Reference"),
            (n2, right, label_b, "Comparison"),
        ):
            with panel:
                try:
                    matrix = neighborhood_matrix(adata, ann, k=min(k, adata.n_obs - 1))
                    st.plotly_chart(
                        px.imshow(matrix, aspect="auto", zmin=0, zmax=1,
                                  title=f"{title} neighborhood fractions"),
                        use_container_width=True
                    )
                except Exception as exc:
                    st.info(f"{title} neighborhood analysis unavailable: {exc}")
    with tabs[4]:
        st.download_button("Download population comparison CSV",
            result["composition"].to_csv(index=False).encode("utf-8"),
            file_name="mbsi_population_comparison.csv", mime="text/csv")
        st.download_button("Download expression comparison CSV",
            result["expression"].to_csv(index=False).encode("utf-8"),
            file_name="mbsi_expression_comparison.csv", mime="text/csv")
        manifest = {
            "input_samples": result["sample_ids"],
            "annotation_columns": result["annotation_keys"],
            "selected_genes": genes,
            "method": "descriptive means on H5AD .X; no batch harmonization",
            "inference": "none",
            "warnings": result["warnings"],
        }
        st.download_button("Download method and limitations JSON",
            json.dumps(manifest, indent=2).encode("utf-8"),
            file_name="mbsi_comparison_manifest.json", mime="application/json")
