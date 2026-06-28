"""Dashboard cards, metrics strip, and export helpers."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import plotly.graph_objects as go
import streamlit as st

logger = logging.getLogger(__name__)

DARK = dict(
    paper_bgcolor="#0d1828",
    plot_bgcolor="#07111f",
    font=dict(color="#f4f7fb", size=10),
    margin=dict(l=30, r=10, t=28, b=30),
)


def render_metric_strip(summary: Dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="mbsi-metric-strip">
          <div class="mbsi-metric-card"><div class="mbsi-metric-value mbsi-mv-blue">{summary['cells']:,}</div>
            <div class="mbsi-metric-label">Reconstructed Cells</div></div>
          <div class="mbsi-metric-card"><div class="mbsi-metric-value mbsi-mv-purple">{summary['cell_types_n']}</div>
            <div class="mbsi-metric-label">Cell Types</div></div>
          <div class="mbsi-metric-card"><div class="mbsi-metric-value mbsi-mv-cyan">{summary['resolution_um']} µm</div>
            <div class="mbsi-metric-label">Spatial Resolution</div></div>
          <div class="mbsi-metric-card"><div class="mbsi-metric-value mbsi-mv-orange">{summary['boundary_leakage']:.2f}</div>
            <div class="mbsi-metric-label">Boundary Leakage Score</div></div>
          <div class="mbsi-metric-card"><div class="mbsi-metric-value mbsi-mv-green">{summary['morans_i']:.2f}</div>
            <div class="mbsi-metric-label">Moran's I Preservation</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def donut_composition(composition_df, title: str = "Cell Type Composition") -> go.Figure:
    fig = go.Figure(data=[go.Pie(
        labels=composition_df["cell_type"], values=composition_df["pct"],
        hole=0.55, textinfo="none",
        marker=dict(colors=[
            "#ff4f7b", "#f7c948", "#4cd964", "#ff9f1a", "#30d5c8",
            "#3b82f6", "#c084fc", "#f97316", "#ec4899", "#a855f7", "#b8c1cc",
        ][: len(composition_df)]),
    )])
    fig.update_layout(title=title, **DARK, showlegend=True,
                      legend=dict(font=dict(size=7), bgcolor="#0d1828"))
    return fig


def pseudotime_scatter(trajectory_df, title: str = "Pseudotime / Trajectory") -> go.Figure:
    fig = go.Figure(data=go.Scatter(
        x=trajectory_df["x"], y=trajectory_df["y"], mode="markers",
        marker=dict(size=4, color=trajectory_df["pseudotime"],
                    colorscale=[[0, "#f7c948"], [1, "#9b6cff"]], showscale=False),
    ))
    fig.update_layout(title=title, **DARK,
                      xaxis=dict(title="Component 1", gridcolor="#22314a"),
                      yaxis=dict(title="Component 2", gridcolor="#22314a"))
    return fig


def causal_ranking(causal_df, title: str = "Causal Driver Ranking") -> go.Figure:
    fig = go.Figure(data=[go.Bar(
        y=causal_df["driver"], x=causal_df["effect"], orientation="h",
        marker=dict(color="#4f7cff"),
        text=[f"+{v:.2f}" for v in causal_df["effect"]], textposition="outside",
    )])
    fig.update_layout(title=title, **DARK, yaxis=dict(autorange="reversed"),
                      xaxis=dict(title="Effect on Outcome", gridcolor="#22314a"))
    return fig


def invasion_heatmap(field, title: str = "Invasion & Boundary Analysis") -> go.Figure:
    fig = go.Figure(data=go.Heatmap(
        z=field, colorscale=[[0, "#07111f"], [0.5, "#ffb020"], [1, "#ff5c7a"]],
        showscale=False,
    ))
    fig.update_layout(title=title, **DARK,
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def treatment_radar(treatment: Dict, baseline: Dict, treatment_name: str) -> go.Figure:
    cats = list(baseline.keys())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[baseline[c] for c in cats] + [baseline[cats[0]]],
        theta=cats + [cats[0]], name="Baseline",
        line=dict(color="#9aa7b8", dash="dash"), fill="toself", opacity=0.2,
    ))
    vals = treatment.get(treatment_name, treatment["Cisplatin"])
    fig.add_trace(go.Scatterpolar(
        r=[vals[c] for c in cats] + [vals[cats[0]]],
        theta=cats + [cats[0]], name="Predicted",
        line=dict(color="#39d98a"), fill="toself", opacity=0.35,
    ))
    fig.update_layout(
        title=f"Digital Twin — {treatment_name}",
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], gridcolor="#22314a"),
                   bgcolor="#07111f"),
        **DARK, showlegend=True, legend=dict(font=dict(size=8)),
    )
    return fig


def export_all(
    demo: Dict[str, Any],
    out_dir: Path = Path("data/outputs"),
    analysis_results: Optional[Dict[str, Any]] = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    demo["cells"].to_csv(out_dir / "dashboard_cells.csv", index=False)
    demo["pathways"].to_csv(out_dir / "pathways.csv", index=False)
    demo["interactions"].to_csv(out_dir / "interactions.csv", index=False)
    demo["causal"].to_csv(out_dir / "causal_drivers.csv", index=False)
    summary = demo.get("summary", {})
    (out_dir / "dashboard_summary.json").write_text(json.dumps(summary, indent=2))
    bundle = out_dir / "dashboard_export.json"
    bundle.write_text(json.dumps({
        "summary": summary,
        "pathways": demo["pathways"].to_dict(orient="records"),
        "causal": demo["causal"].to_dict(orient="records"),
    }, indent=2))

    if analysis_results is None:
        try:
            from mbsi.analysis.demo import make_synthetic_visium_adata
            from mbsi.analysis.pipeline import run_standard_spatial_analysis, export_analysis_results

            adata = make_synthetic_visium_adata(n_spots=60, n_genes=120, seed=42)
            analysis_results = run_standard_spatial_analysis(
                adata,
                min_counts=0,
                min_genes=0,
                max_mito=100.0,
                n_top_genes=60,
                n_comps=10,
                n_neighbors=10,
                n_pcs=5,
                spatial_stats_top_n=30,
            )
            export_analysis_results(analysis_results, out_dir=out_dir)
        except Exception as exc:
            logger.warning("Analysis export failed: %s", exc)
    elif analysis_results:
        from mbsi.analysis.pipeline import export_analysis_results

        export_analysis_results(analysis_results, out_dir=out_dir)

    try:
        from mbsi.communication import run_communication_analysis, export_communication_results, make_communication_demo_adata

        comm = run_communication_analysis(make_communication_demo_adata(seed=42))
        export_communication_results(comm, out_dir=out_dir)
    except Exception as exc:
        logger.warning("Communication export failed: %s", exc)

    try:
        from mbsi.tme import run_tme_analysis, export_tme_results, generate_spatial_biomarker_report, make_tme_demo_adata

        tme = run_tme_analysis(make_tme_demo_adata(seed=42))
        export_tme_results(tme, out_dir=out_dir)
        generate_spatial_biomarker_report(tme, out_dir=out_dir)
    except Exception as exc:
        logger.warning("TME export failed: %s", exc)

    return out_dir
