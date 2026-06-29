"""Discovery workspace — Finding → Evidence → Confidence."""

import streamlit as st
from app.components.interactive_figures import render_interactive_plot
from app.components.page_utils import OUTPUT_DIR
from app.components.safe import safe_get
from app.workspaces._helpers import add_finding, demo_banner, safe_register_finding
from mbsi.discovery import export_discovery_engine, run_discovery_engine


def _confidence_badge(level: str) -> str:
    colors = {
        "High": "#22c55e",
        "Moderate": "#3b82f6",
        "Exploratory": "#f59e0b",
        "Hypothesis": "#94a3b8",
    }
    color = colors.get(level, "#94a3b8")
    return f'<span style="background:{color};color:#07111f;padding:2px 8px;border-radius:4px;font-size:0.8em;font-weight:600;">{level}</span>'


def _run_discovery() -> None:
    seed = int(st.session_state.get("ctx_discovery_seed", 42))
    readiness = st.session_state.get("mbsi_readiness")
    try:
        out = run_discovery_engine(seed=seed, readiness=readiness)
        st.session_state.discovery_results = out
        st.session_state.findings = out.get("findings", [])
        st.session_state.evidence = out.get("evidence", [])
        st.session_state.discovery_graph = out.get("discovery_graph")
        st.session_state.benchmark_results = out.get("benchmark_results")
        st.session_state.communication_results = out.get("communication_results")
        st.session_state.tme_results = out.get("tme_results")
        export_discovery_engine(out, OUTPUT_DIR)
        st.session_state.last_run = "Discovery Engine"
        for w in out.get("warnings", []):
            st.session_state.setdefault("saas_warnings", []).append(w)
        for f in out.get("findings", [])[:5]:
            add_finding(f.get("title", "Finding"), f.get("summary", ""), module="discovery")
            safe_register_finding(
                f.get("summary", ""),
                section="discovery",
                module="discovery",
                title=f.get("title", "Finding"),
            )
        safe_register_finding(
            f"Discovery: {len(out.get('findings', []))} findings, status {out.get('status')}",
            section="discovery",
            module="discovery",
            title="Pipeline complete",
        )
    except Exception as exc:
        st.warning(f"Discovery failed: {exc}")


def _render_top_findings(findings: list, evidence: list, benchmark: dict) -> None:
    st.markdown("### Top Findings")
    evidence_by_id = {e.get("evidence_id"): e for e in evidence}
    bench_support = 0.0
    lb = safe_get(benchmark, "leaderboard") if benchmark else None
    if lb is not None and hasattr(lb, "empty") and not lb.empty:
        bench_support = float(lb.iloc[0].get("gene_pearson", 0)) * 100

    sorted_findings = sorted(findings, key=lambda f: f.get("confidence_score", 0), reverse=True)
    for f in sorted_findings[:8]:
        level = f.get("confidence_level", "Hypothesis")
        score = f.get("confidence_score", 0)
        st.markdown(
            f"**{f.get('title')}** {_confidence_badge(level)} · {score:.0f}/100",
            unsafe_allow_html=True,
        )
        st.caption(f"{f.get('finding_type')} · {f.get('module')}")
        if bench_support > 0:
            st.caption(f"Benchmark support: {bench_support:.0f}%")
        with st.expander("Evidence", expanded=False):
            for eid in f.get("evidence_ids", []):
                ev = evidence_by_id.get(eid)
                if ev:
                    st.markdown(f"- **{ev.get('title')}** ({ev.get('evidence_type')}) — {ev.get('description', '')}")


def render():
    using_demo = st.session_state.get("using_synthetic_demo", True)
    platform = st.session_state.get("mbsi_platform")
    if using_demo:
        demo_banner()
        st.warning("Discovery runs on demo orchestration — upload real data for dataset-specific insights.")
    elif platform:
        readiness = st.session_state.get("mbsi_readiness", {})
        st.success(f"Real data loaded ({platform}) — readiness: {readiness.get('status', 'unknown')}")

    action = st.session_state.pop("ribbon_action", None)
    if action == "run_discovery":
        _run_discovery()
    elif action == "export_discovery":
        st.toast("Discovery summary added to notebook for export.")

    st.markdown("### Biopharma Discovery Engine")
    st.caption("Finding → Evidence → Confidence → Report")
    if st.button("Run Discovery Pipeline", type="primary", key="ws_run_discovery"):
        _run_discovery()

    results = st.session_state.get("discovery_results")
    findings = st.session_state.get("findings") or (results or {}).get("findings", [])
    if not results and not findings:
        st.info("Run full discovery pipeline.")
        return

    st.metric("Status", results.get("status", "unknown") if results else "loaded")
    st.metric("Findings", len(findings))

    evidence = st.session_state.get("evidence") or (results or {}).get("evidence", [])
    benchmark = results.get("benchmark_results") if results else st.session_state.get("benchmark_results")
    _render_top_findings(findings, evidence, benchmark)

    validations = (results or {}).get("validation_recommendations", [])
    if validations:
        with st.expander("Validation recommendations"):
            for v in validations[:5]:
                st.markdown(f"**{v.get('title')}**")
                for rec in v.get("recommendations", [])[:2]:
                    st.caption(f"• {rec}")

    lb = safe_get(benchmark, "leaderboard") if benchmark else None
    if lb is not None and hasattr(lb, "empty") and not lb.empty:
        from mbsi.visualization.benchmark_plots import plot_leaderboard_bars
        render_interactive_plot(plot_leaderboard_bars(lb), title="Discovery Benchmark", module="discovery", key="disc_bench")
