"""MBSI Studio Explore: white, linked, multi-sample spatial browser."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from mbsi.visualization.browser_contract import (
    AnnDataBrowserAdapter, SpatialView, resolve_browser_samples,
)

_PURPLE = "#6d28d9"


def _figure(view: SpatialView, *, selected: set[str] | None = None,
            height: int = 460, compact: bool = False) -> go.Figure:
    """Real observed points; WebGL for large arrays, sample-local coordinates."""
    fig = go.Figure()
    if view.categorical:
        categories = sorted(set(map(str, view.values)))
        for category in categories:
            idx = np.asarray(view.values, dtype=str) == category
            fig.add_trace(go.Scattergl(
                x=view.x[idx], y=view.y[idx], mode="markers", name=category,
                customdata=np.asarray(view.barcodes, dtype=object)[idx],
                marker=dict(size=4 if compact else 6, opacity=0.88),
                hovertemplate="%{customdata}<extra>" + category + "</extra>",
            ))
    else:
        values = np.asarray(view.values, dtype=float)
        fig.add_trace(go.Scattergl(
            x=view.x, y=view.y, mode="markers",
            customdata=list(view.barcodes),
            marker=dict(size=3 if compact else 5, color=values, colorscale="Viridis",
                        cmin=float(np.min(values)), cmax=float(np.max(values)) if np.max(values)>np.min(values) else float(np.min(values))+1,
                        opacity=0.93, showscale=not compact,
                        colorbar=dict(title=view.label, thickness=11)),
            hovertemplate="Spot %{customdata}<br>Value %{marker.color:.3f}<extra></extra>",
            name=view.label,
        ))
    if selected:
        idx = np.isin(np.asarray(view.barcodes), list(selected))
        if idx.any():
            fig.add_trace(go.Scattergl(
                x=view.x[idx], y=view.y[idx], mode="markers",
                marker=dict(size=10, color="rgba(0,0,0,0)", line=dict(color="#f97316", width=2)),
                hoverinfo="skip", name="Selected spots",
            ))
    fig.update_layout(
        height=height, margin=dict(l=5, r=5, t=32, b=5),
        title=dict(text=view.sample_id, font=dict(size=14)),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(color="#334155", size=12),
        dragmode="lasso", legend=dict(orientation="h", y=-0.13),
        showlegend=view.categorical and not compact,
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, autorange="reversed"),
    )
    return fig


def _selected_barcodes(event) -> set[str]:
    if not event or not getattr(event, "selection", None):
        return set()
    points = event.selection.get("points", [])
    return {str(point["customdata"]) for point in points if point.get("customdata") is not None}


def _navigate(module: str) -> None:
    st.session_state.active_module = module
    st.rerun()


def render() -> None:
    st.markdown("""
    <style>
      .stApp:has(.mbsi-browser-anchor) {background:#f8fafc !important;color:#1e293b}
      .stApp:has(.mbsi-browser-anchor) .saas-app {--mbsi-bg:#f8fafc;--mbsi-surface:#fff;--mbsi-surface-alt:#f8fafc;--mbsi-text:#1e293b;--mbsi-muted:#64748b;--mbsi-border:#e2e8f0;--mbsi-accent:#6d28d9}
      .stApp:has(.mbsi-browser-anchor) div[data-testid="stPlotlyChart"] {background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:5px}
      .stApp:has(.mbsi-browser-anchor) div[data-testid="stTabs"] {background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:10px}
      .stApp:has(.mbsi-browser-anchor) .stButton>button[kind="primary"] {background:#6d28d9!important;border-color:#6d28d9!important;color:#fff!important}
    </style>
    <div class="mbsi-browser-anchor"></div>
    """, unsafe_allow_html=True)
    st.markdown("### Explore · Spatial Browser")
    st.caption("Linked tissue maps and sample comparisons • observed data only")
    if st.session_state.get("using_synthetic_demo"):
        st.warning("Developer-mode synthetic data are active. Browser values are simulated, not measured.")
    try:
        samples = resolve_browser_samples(st.session_state)
        if not samples:
            st.info("No spatial dataset loaded. Upload and ingest data in Study & Data.")
            if st.button("Open Study & Data", key="browser_upload"):
                _navigate("study_data")
            return
        adapter = AnnDataBrowserAdapter(samples)
    except (ValueError, OSError, KeyError) as exc:
        st.error(f"Spatial browser input is not ready: {exc}")
        return

    ids = adapter.samples()
    gene_list = adapter.genes()
    features = adapter.features()
    toolbar = st.columns([2.3, 1.6, 1.1, 1.1])
    with toolbar[0]:
        selected_ids = st.multiselect("Samples", ids, default=ids[:min(4, len(ids))],
                                      key="browser_samples")
    with toolbar[1]:
        mode = st.selectbox("Color by", ["Gene expression"] + features,
                            key="browser_color_mode")
    with toolbar[2]:
        st.selectbox("Comparison", ["By sample", "Summary table"],
                     key="browser_compare_mode")
    with toolbar[3]:
        st.selectbox("Spot size", ["Auto", "Small", "Large"], key="browser_point_size")
    if not selected_ids:
        st.info("Select at least one sample.")
        return
    if mode == "Gene expression":
        if not gene_list:
            st.warning("The selected samples have no shared genes.")
            return
        default_gene = "CD8A" if "CD8A" in gene_list else gene_list[0]
        gene = st.selectbox("Search gene", gene_list, index=gene_list.index(default_gene),
                            key="browser_gene")
        feature = gene
    else:
        feature = mode

    selected_id = st.selectbox("Main tissue", selected_ids, key="browser_main_sample")
    if st.session_state.get("browser_selection_sample") != selected_id:
        st.session_state["browser_selected_barcodes"] = set()
        st.session_state["browser_selection_sample"] = selected_id
    primary = adapter.view(selected_id, feature)
    main, compare, info = st.columns([4.6, 3.4, 2.0], gap="small")
    with main:
        st.markdown("**Spatial tissue map**")
        main_figure = _figure(primary, selected=st.session_state.get("browser_selected_barcodes"),
                              height=540)
        try:
            event = st.plotly_chart(main_figure, use_container_width=True,
                                    key="browser_main_plot", on_select="rerun",
                                    selection_mode=("points", "lasso", "box"))
        except TypeError:
            # Streamlit 1.28-1.34 predates Plotly selection events.
            st.plotly_chart(main_figure, use_container_width=True,
                            key="browser_main_plot_legacy")
            st.caption("Update Streamlit to >=1.35 for interactive lasso selection.")
            event = None
        new_selection = _selected_barcodes(event)
        if new_selection:
            st.session_state["browser_selected_barcodes"] = new_selection
        with st.expander("Selected tissue region", expanded=False):
            selected = st.session_state.get("browser_selected_barcodes", set())
            st.caption(f"{len(selected)} selected spots/cells in {selected_id}. Selection is local to this sample.")
            if st.button("Clear selection", key="browser_clear"):
                st.session_state["browser_selected_barcodes"] = set()
                st.rerun()
    with compare:
        st.markdown("**Compare samples**")
        if st.session_state.get("browser_compare_mode") == "Summary table":
            st.dataframe(pd.DataFrame(adapter.summary(feature)), use_container_width=True,
                         hide_index=True)
        else:
            columns = st.columns(2, gap="small")
            for i, sid in enumerate(selected_ids):
                with columns[i % 2]:
                    st.plotly_chart(_figure(adapter.view(sid, feature), compact=True, height=245),
                                    use_container_width=True, key=f"browser_tile_{i}")
    with info:
        st.markdown("**Feature information**")
        st.markdown(f"#### {feature}")
        st.caption("Measured values from loaded data" if mode == "Gene expression" else "Existing sample annotation")
        st.metric("Samples", len(selected_ids))
        st.metric("Spots / cells", f"{sum(samples[s].n_obs for s in selected_ids):,}")
        if mode == "Gene expression":
            rows = pd.DataFrame(adapter.summary(feature))
            st.markdown("**Mean expression**")
            st.bar_chart(rows.set_index("sample_id")["mean_expression"], color=_PURPLE)
            st.caption("Descriptive only; no differential-expression significance implied.")
        else:
            st.caption("Categorical annotations are supplied by the source dataset.")
    st.divider()
    st.markdown("**Advanced analyses**")
    tabs = st.tabs(["SpatialGE", "Differential", "Enrichment", "Niches", "Gradients", "Domains"])
    destinations = [
        ("SpatialGE", "study_data", "Open the optional spatialGE R engine in Study & Data."),
        ("Differential", "differential_analysis", "Biological-replicate-aware differential analysis."),
        ("Enrichment", "spatial_gene_sets", "Spatial gene-set and pathway enrichment."),
        ("Niches", "discovery", "Explore tissue microenvironments and neighborhoods."),
        ("Gradients", "spatial_gradients", "Explore spatial expression gradients."),
        ("Domains", "spatial_domains", "Explore tissue domain identification."),
    ]
    for tab, (name, target, description) in zip(tabs, destinations):
        with tab:
            st.caption(description)
            if st.button(f"Open {name}", key=f"browser_open_{name}"):
                _navigate(target)
