import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from app.components.layout import inject_styles
from app.components.page_utils import (
    init_session, guardrail_banner, ensure_adata, save_reconstructed, OUTPUT_DIR,
)
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from app.components.parameter_panels import mbsi_parameter_panel, run_mode_selector
from mbsi.reconstruction.solver import run_mbsi, run_iterative_mbsi

st.set_page_config(page_title="Run MBSI | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
guardrail_banner()
ensure_adata(show_warning=False)

render_topnav(active="Run MBSI")

st.markdown("### Run MBSI Reconstruction")
mode = run_mode_selector()
params = mbsi_parameter_panel()
st.checkbox("GPU toggle (placeholder)", value=False, disabled=True, help="GPU support coming soon")

if st.button("Start Reconstruction", type="primary"):
    with st.spinner("Running MBSI..."):
        fn = run_iterative_mbsi if mode == "Publication-Quality Run" else run_mbsi
        kw = dict(
            n_cells_per_spot=params["n_cells_per_spot"], gamma=params["gamma"],
            epsilon=params["epsilon"], lambda_sheaf=params["lambda_sheaf"],
            rho1=params["rho1"], rho2=params["rho2"], use_sheaf=params["use_sheaf"],
            use_anisotropic=params["use_anisotropic"], k_graph=params["k_graph"],
            random_state=params["random_seed"],
        )
        if fn == run_mbsi:
            kw["max_iter"] = params["max_iter"]
        else:
            kw["max_outer_iter"] = 5
            kw["max_inner_iter"] = max(10, params["max_iter"] // 5)
        from app.components.histology_viewer import get_active_histology_image, sync_histology_session_from_adata

        sync_histology_session_from_adata(st.session_state.adata)
        img, _ = get_active_histology_image(st.session_state.adata)
        st.session_state.reconstructed = fn(st.session_state.adata, image=img, **kw)
        path = save_reconstructed()
    st.session_state.last_run = "MBSI reconstruction"
    st.success(f"Reconstructed {st.session_state.reconstructed.n_obs} cells → {path}")

if st.session_state.reconstructed is not None:
    coords = st.session_state.reconstructed.obsm.get("spatial")
    if coords is not None:
        st.scatter_chart({"x": coords[:500, 0], "y": coords[:500, 1]})

render_statusbar(show_actions=False)
