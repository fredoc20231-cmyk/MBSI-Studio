"""Communication Intelligence — spatial L-R signaling analysis."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from app.components.layout import inject_styles
from app.components.page_utils import init_session, ensure_adata, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.communication import (
    run_communication_analysis,
    export_communication_results,
    make_communication_demo_adata,
    load_builtin_ligand_receptor_pairs,
    compute_diffusion_weighted_signaling,
    build_sender_receiver_network,
    compute_niche_signaling_maps,
    generate_communication_report,
    COMMUNICATION_GUARDRAIL,
)
from mbsi.visualization.communication_plots import (
    plot_signaling_map,
    plot_pathway_rankings,
    plot_sender_receiver_network,
)

st.set_page_config(
    page_title="Communication Intelligence | MBSI Studio",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_session()
inject_styles()
ensure_adata(show_warning=False)

render_topnav(active="Comms")

st.markdown("## Communication Intelligence")
st.caption(COMMUNICATION_GUARDRAIL)
st.caption("Computational hypothesis — not validated pathway activity.")

ctrl, main = st.columns([1, 3])

with ctrl:
    st.markdown("**L-R Catalog**")
    catalog = load_builtin_ligand_receptor_pairs()
    st.dataframe(catalog, use_container_width=True, hide_index=True, height=180)

    use_demo = st.checkbox("Use synthetic demo data", value=True)
    k_neighbors = st.slider("Spatial neighbors (k)", 3, 15, 6)

    if st.button("Run Communication Analysis", type="primary", use_container_width=True):
        adata = make_communication_demo_adata(seed=42) if use_demo else st.session_state.adata
        if adata is None:
            st.error("No data loaded.")
        else:
            with st.spinner("Scoring ligand-receptor pathways..."):
                results = run_communication_analysis(adata, k=k_neighbors)
                st.session_state.communication_results = results
                st.session_state.communication_result = results
                export_communication_results(results, OUTPUT_DIR)
                st.session_state.last_run = "Communication analysis"
            st.success(f"Top pathway: {results.get('top_pathway', 'N/A')}")

    if st.button("Export CSVs + Report", use_container_width=True):
        if st.session_state.get("communication_results"):
            export_communication_results(st.session_state.communication_results, OUTPUT_DIR)
            path = generate_communication_report(st.session_state.communication_results, OUTPUT_DIR)
            st.success(f"Exported to {OUTPUT_DIR} | Report: {path}")
        else:
            st.warning("Run analysis first.")

with main:
    results = st.session_state.get("communication_results")
    if results is None:
        st.info(
            "Run Communication Analysis to score CXCL12-CXCR4, TGFB1-TGFBR, "
            "PD-L1-PD1, VEGFA-VEGFR2, MIF-CD74, CCL5-CCR5, and IL6-IL6R."
        )
        st.stop()

    t1, t2, t3, t4, t5 = st.tabs([
        "Pathway Rankings", "Sender / Receiver", "Diffusion Flux",
        "Niche Maps", "Spatial Map",
    ])

    with t1:
        rankings = results["pathway_rankings"]
        st.dataframe(rankings, use_container_width=True, hide_index=True)
        st.plotly_chart(
            plot_pathway_rankings(rankings),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with t2:
        sr = results.get("sender_receiver")
        if sr is not None and not sr.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Top senders**")
                st.dataframe(sr.nlargest(15, "sender_score"), use_container_width=True, hide_index=True)
            with c2:
                st.markdown("**Top receivers**")
                st.dataframe(sr.nlargest(15, "receiver_score"), use_container_width=True, hide_index=True)
        net = plot_sender_receiver_network(results.get("edges"))
        if net:
            st.plotly_chart(net, use_container_width=True, config={"displayModeBar": False})

    with t3:
        flux = results.get("flux_field")
        if flux is not None:
            st.json({k: str(v)[:80] if not isinstance(v, (int, float, str)) else v for k, v in flux.items() if k != "values"})
        else:
            st.caption("Diffusion flux computed for top pathway when genes present.")

    with t4:
        if results.get("top_pathway") and st.session_state.get("adata") is not None:
            top = results["pathway_rankings"].iloc[0]
            niche_maps = compute_niche_signaling_maps(
                st.session_state.adata,
                pairs=[(top["ligand"], top["receptor"])],
            )
            st.write(f"Computed {len(niche_maps)} niche map(s)")

    with t5:
        niche = results.get("niche_map")
        if niche:
            pathway = niche.get("pathway", results.get("top_pathway", ""))
            st.plotly_chart(
                plot_signaling_map(niche, title=f"Signaling Flux — {pathway}"),
                use_container_width=True,
                config={"displayModeBar": False},
            )

render_statusbar(show_actions=False)
