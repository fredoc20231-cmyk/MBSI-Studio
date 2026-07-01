"""Discovery Intelligence workspace — real-data first."""

import streamlit as st

from app.components.notification_center import push_notification
from app.components.page_header import render_page_header
from app.components.page_utils import OUTPUT_DIR, load_advanced_demo_into_session
from app.components.safe import safe_get
from app.workspaces._discovery_runners import run_communication, run_tme
from mbsi.discovery import export_discovery_engine
from mbsi.schema.workflow import WORKFLOW_SUBSTEPS, WorkflowModule
from mbsi.workflows.discover import run_discover_workflow


def _confidence_badge(level: str) -> str:
    colors = {
        "High": "#22c55e",
        "Moderate": "#3b82f6",
        "Exploratory": "#f59e0b",
        "Hypothesis": "#94a3b8",
    }
    color = colors.get(level, "#94a3b8")
    return f'<span style="background:{color};color:#07111f;padding:2px 8px;border-radius:4px;font-size:0.8em;font-weight:600;">{level}</span>'


def _has_real_adata() -> bool:
    return st.session_state.get("adata") is not None and not st.session_state.get("using_synthetic_demo", False)


def _run_discovery(allow_demo: bool = False) -> None:
    seed = int(st.session_state.get("ctx_discovery_seed", 42))
    readiness = st.session_state.get("mbsi_readiness")
    adata = st.session_state.get("adata") if _has_real_adata() or allow_demo else None
    run = run_discover_workflow(
        adata=adata,
        readiness=readiness,
        seed=seed,
        allow_demo=allow_demo,
        analysis_results=st.session_state.get("analysis_results"),
    )
    if run.status != "success":
        msg = run.warnings[0] if run.warnings else "Discovery unavailable — upload real data first"
        push_notification(msg, title="Discovery failed", level="warning", source="discovery")
        st.warning(msg)
        return
    out = run.outputs.get("discovery_results", {})
    st.session_state.discovery_results = out
    st.session_state.findings = out.get("findings", [])
    st.session_state.evidence = out.get("evidence", [])
    st.session_state.discovery_graph = out.get("discovery_graph")
    st.session_state.benchmark_results = out.get("benchmark_results")
    st.session_state.communication_results = out.get("communication_results")
    st.session_state.tme_results = out.get("tme_results")
    export_discovery_engine(out, OUTPUT_DIR)
    st.session_state.last_run = "Discovery Intelligence"
    st.session_state.run_outputs["discovery"] = run.to_dict()
    push_notification(
        f"{len(st.session_state.findings)} findings registered.",
        title="Discovery complete",
        level="success",
        source="discovery",
    )


def _render_top_findings(findings: list, evidence: list) -> None:
    st.markdown("### Top Findings")
    evidence_by_id = {e.get("evidence_id"): e for e in evidence}
    sorted_findings = sorted(findings, key=lambda f: f.get("confidence_score", 0), reverse=True)
    for f in sorted_findings[:8]:
        level = f.get("confidence_level", "Hypothesis")
        score = f.get("confidence_score", 0)
        ctx = []
        if f.get("sample_id"):
            ctx.append(f"sample={f['sample_id']}")
        if f.get("run_id"):
            ctx.append(f"run={f['run_id'][:8]}…")
        ctx_str = f" ({', '.join(ctx)})" if ctx else ""
        st.markdown(
            f"**{f.get('title')}** {_confidence_badge(level)} · {score:.0f}/100{ctx_str}",
            unsafe_allow_html=True,
        )
        with st.expander("Evidence", expanded=False):
            for eid in f.get("evidence_ids", []):
                ev = evidence_by_id.get(eid)
                if ev:
                    st.markdown(f"- **{ev.get('title')}** — {ev.get('description', '')}")


def render():
    render_page_header(
        "Discovery Intelligence",
        "Integrate findings, communication, TME niches, and causal hypotheses.",
        icon="💡",
    )
    adata = st.session_state.get("adata")

    if not _has_real_adata() and adata is None:
        st.warning("Discovery unavailable — upload real data in Study Setup & Data first.")
        if st.button("Load Demo Dataset (labeled demo)", key="disc_load_demo"):
            load_advanced_demo_into_session(force=True)
            st.session_state.using_synthetic_demo = True
            st.session_state.mbsi_platform = "demo"
            st.session_state.mbsi_readiness = {"status": "Synthetic demo data", "technology_key": "demo"}
            st.rerun()
        return

    substeps = WORKFLOW_SUBSTEPS[WorkflowModule.DISCOVERY.value]
    tab_labels = [s.replace("_", " ").title() for s in substeps]
    tabs = st.tabs(tab_labels)

    with tabs[0]:
        st.caption("L-R signaling and pathway communication")
        if st.button("Run Communication", key="disc_run_comm"):
            run_communication()
        results = st.session_state.get("communication_results")
        if results:
            rankings = results.get("pathway_rankings")
            if rankings is not None and hasattr(rankings, "empty") and not rankings.empty:
                st.dataframe(rankings.head(10), use_container_width=True)

    with tabs[1]:
        st.caption("TME niche detection")
        if st.button("Run TME Niches", key="disc_run_tme"):
            run_tme()
        tme = st.session_state.get("tme_results")
        if tme and tme.get("summary") is not None:
            st.dataframe(tme["summary"], use_container_width=True)

    niche_tabs = {
        2: "Immune exclusion scoring (requires real data + niche run)",
        3: "CAF barrier niches (requires real data + niche run)",
        4: "TLS detection (requires real data + niche run)",
        5: "Hypoxia niches (requires real data + niche run)",
        6: "Angiogenesis fronts (requires real data + niche run)",
        7: "Invasion fronts (requires real data + niche run)",
    }
    for idx, caption in niche_tabs.items():
        with tabs[idx]:
            st.info(caption)

    with tabs[8]:
        st.caption("Spatial biomarker panels")
        if st.button("Run full Discovery Engine", type="primary", key="disc_run_engine"):
            _run_discovery(allow_demo=False)

    with tabs[9]:
        st.caption("Causal driver hypotheses from discovery graph")

    with tabs[10]:
        recs = safe_get(st.session_state.get("discovery_results"), "validation_recommendations")
        if recs:
            for r in recs[:5]:
                st.markdown(f"- {r.get('title', r)}")
        else:
            st.info("Run Discovery Engine for validation recommendations.")

    findings = st.session_state.get("findings") or []
    evidence = st.session_state.get("evidence") or []
    if findings:
        st.divider()
        _render_top_findings(findings, evidence)
