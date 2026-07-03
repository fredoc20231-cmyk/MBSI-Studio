import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import numpy as np
from app.components.layout import inject_styles
from app.components.page_utils import init_session, guardrail_banner, ensure_adata, OUTPUT_DIR
from app.components.topnav import render_topnav
from app.components.statusbar import render_statusbar
from mbsi.segmentation import (
    segment_tissue, segment_nuclei, infer_cell_boundaries,
    assign_spots_to_compartments, voronoi_cell_regions,
)

st.set_page_config(page_title="Segmentation | MBSI Studio", layout="wide", initial_sidebar_state="collapsed")

init_session()
inject_styles()
guardrail_banner()
ensure_adata(show_warning=False)

render_topnav(active="Segmentation")

st.markdown("### Tissue Segmentation")
method = st.selectbox("Method", ["coordinate (Voronoi fallback)", "image"])

if st.button("Run Segmentation", type="primary"):
    adata = st.session_state.adata
    from app.components.histology_viewer import get_active_histology_image, sync_histology_session_from_adata

    sync_histology_session_from_adata(adata)
    img, img_source = get_active_histology_image(adata)
    use_image = img is not None and "image" in method
    if use_image:
        try:
            tissue = segment_tissue(img)
            nuclei = segment_nuclei(img)
            boundaries = infer_cell_boundaries(image=img, nuclei_mask=nuclei)
            st.session_state.segmentation_result = {
                "method": "image", "tissue_shape": tissue.shape, "n_nuclei": int(nuclei.max()),
            }
        except Exception as exc:
            st.warning(f"Image segmentation failed ({exc}); using Voronoi fallback.")
            use_image = False
    if not use_image:
        regions = voronoi_cell_regions(adata.obsm["spatial"])
        adata = assign_spots_to_compartments(adata, regions)
        st.session_state.adata = adata
        st.session_state.segmentation_result = {"method": "voronoi", "n_regions": len(regions)}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(OUTPUT_DIR / "segmented_spots.h5ad")
    st.session_state.last_run = "Segmentation"
    st.success("Segmentation complete.")

if st.session_state.segmentation_result:
    st.json(st.session_state.segmentation_result)

if st.session_state.adata is not None:
    coords = st.session_state.adata.obsm["spatial"]
    st.scatter_chart({"x": coords[:, 0], "y": coords[:, 1]})

render_statusbar(show_actions=False)
