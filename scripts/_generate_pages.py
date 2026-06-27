"""Generate Streamlit pages for MBSI Studio v2."""
from pathlib import Path

PAGES = Path("app/pages")
PAGES.mkdir(parents=True, exist_ok=True)

HEADER = '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
import numpy as np
from app.components.page_utils import init_session, guardrail_banner, require_adata, require_reconstructed, causal_warning, simulation_warning

init_session()
guardrail_banner()
'''

pages = {}

pages["01_Dashboard.py"] = HEADER + '''
st.title("MBSI Studio Dashboard")
st.markdown("**Physics-Aware Spatial Biology Intelligence**")
steps = ["Upload", "QC", "Segmentation", "MBSI", "Validation", "Interpretation", "Export"]
st.progress(min(1.0, sum([
    st.session_state.adata is not None,
    bool(st.session_state.preprocessing_params),
    bool(st.session_state.segmentation_result),
    st.session_state.reconstructed is not None,
    bool(st.session_state.metrics),
    bool(st.session_state.analysis_state),
]) / len(steps)))
st.caption(" → ".join(steps))

c1,c2,c3,c4 = st.columns(4)
c1.metric("Spots", st.session_state.adata.n_obs if st.session_state.adata else 0)
c2.metric("Reconstructed Cells", st.session_state.reconstructed.n_obs if st.session_state.reconstructed else 0)
c3.metric("Genes", st.session_state.adata.n_vars if st.session_state.adata else 0)
c4.metric("Validation Score", f"{st.session_state.metrics.get('pearson_correlation', 0):.3f}" if st.session_state.metrics else "N/A")

if st.button("Load Advanced Demo", type="primary"):
    import anndata as ad
    p = Path("data/demo/advanced")
    if (p / "pseudo_visium_spots.h5ad").exists():
        st.session_state.adata = ad.read_h5ad(p / "pseudo_visium_spots.h5ad")
        st.session_state.true_adata = ad.read_h5ad(p / "true_single_cell.h5ad")
        if (p / "reconstructed.h5ad").exists():
            st.session_state.reconstructed = ad.read_h5ad(p / "reconstructed.h5ad")
        import json
        if (p / "analysis_state.json").exists():
            st.session_state.analysis_state = json.loads((p / "analysis_state.json").read_text())
        if (p / "metrics.json").exists():
            st.session_state.metrics = json.loads((p / "metrics.json").read_text())
        st.success("Advanced demo loaded!")
        st.rerun()
    else:
        st.warning("Run: python scripts/run_advanced_demo.py")
'''

pages["02_Upload_Data.py"] = HEADER + '''
from app.components.uploaders import upload_panel, data_readiness_score
st.title("Upload Data")
result = upload_panel()
if result.get("adata") is not None:
    st.session_state.adata = result["adata"]
if result.get("image") is not None:
    st.session_state.uploaded_image = result["image"]
if result.get("segmentation") is not None:
    st.session_state.uploaded_segmentation = result["segmentation"]
if result.get("ground_truth") is not None:
    st.session_state.ground_truth = result["ground_truth"]
if st.session_state.adata is not None:
    score, msg = data_readiness_score(st.session_state.adata)
    st.metric("Data Readiness", f"{score}/100", msg)
'''

pages["03_Preprocessing_QC.py"] = HEADER + '''
from app.components.parameter_panels import preprocessing_parameter_panel
require_adata()
st.title("Preprocessing & QC")
st.session_state.preprocessing_params = preprocessing_parameter_panel()
st.success("Preprocessing parameters saved.")
'''

pages["04_Segmentation.py"] = HEADER + '''
from mbsi.segmentation import segment_tissue, segment_nuclei, infer_cell_boundaries, assign_spots_to_compartments, voronoi_cell_regions
require_adata()
st.title("Segmentation")
method = st.selectbox("Method", ["coordinate", "image"])
if st.button("Run Segmentation"):
    adata = st.session_state.adata
    img = st.session_state.uploaded_image
    if img is not None and method == "image":
        tissue = segment_tissue(img)
        nuclei = segment_nuclei(img)
        boundaries = infer_cell_boundaries(image=img, nuclei_mask=nuclei)
        st.session_state.segmentation_result = {"tissue": tissue, "nuclei": nuclei, "boundaries": boundaries}
    else:
        regions = voronoi_cell_regions(adata.obsm["spatial"])
        adata = assign_spots_to_compartments(adata, regions)
        st.session_state.adata = adata
        st.session_state.segmentation_result = {"regions": regions, "method": "voronoi"}
    st.success("Segmentation complete (reconstruction estimate)")
if st.session_state.segmentation_result:
    st.json({k: str(type(v)) for k,v in st.session_state.segmentation_result.items()})
'''

pages["05_Morphology_Physics.py"] = HEADER + '''
from app.components.parameter_panels import morphology_parameter_panel
from app.components.plots import spatial_plot
require_adata()
st.title("Morphology Physics")
st.session_state.morphology_params = morphology_parameter_panel()
coords = st.session_state.adata.obsm["spatial"]
st.scatter_chart({"x": coords[:,0], "y": coords[:,1]})
st.caption("Diffusion tensor field computed during MBSI when H&E image provided.")
'''

pages["06_Run_MBSI.py"] = HEADER + '''
from app.components.parameter_panels import mbsi_parameter_panel, run_mode_selector
from mbsi.reconstruction.solver import run_mbsi, run_iterative_mbsi
require_adata()
st.title("Run MBSI")
mode = run_mode_selector()
params = mbsi_parameter_panel()
use_gpu = st.checkbox("GPU toggle (placeholder)", value=False)
if st.button("Start Reconstruction", type="primary"):
    with st.spinner("Running MBSI..."):
        fn = run_iterative_mbsi if mode == "Publication-Quality Run" else run_mbsi
        kw = dict(n_cells_per_spot=params["n_cells_per_spot"], gamma=params["gamma"], epsilon=params["epsilon"],
                  lambda_sheaf=params["lambda_sheaf"], rho1=params["rho1"], rho2=params["rho2"],
                  use_sheaf=params["use_sheaf"], use_anisotropic=params["use_anisotropic"],
                  k_graph=params["k_graph"], random_state=params["random_seed"])
        if fn == run_mbsi:
            kw["max_iter"] = params["max_iter"]
        else:
            kw["max_outer_iter"] = 5
            kw["max_inner_iter"] = params["max_iter"] // 5
        st.session_state.reconstructed = fn(st.session_state.adata, image=st.session_state.uploaded_image, **kw)
    st.success(f"Reconstructed {st.session_state.reconstructed.n_obs} cells")
'''

pages["07_Subcellular_Reconstruction.py"] = HEADER + '''
from mbsi.subcellular import infer_subcellular_compartments, partition_transcripts_by_compartment
require_reconstructed()
st.title("Subcellular Reconstruction")
if st.button("Run Subcellular Inference"):
    sub = infer_subcellular_compartments(st.session_state.reconstructed, st.session_state.uploaded_image)
    st.session_state.reconstructed = partition_transcripts_by_compartment(st.session_state.reconstructed, sub)
    st.session_state.subcellular_result = sub
    st.success("Inferred compartment-level estimates")
if st.session_state.subcellular_result:
    for k in ["nuclear_score", "cytoplasmic_score", "membrane_score"]:
        if k in st.session_state.subcellular_result:
            st.line_chart(st.session_state.subcellular_result[k][:50])
'''

pages["08_Boundary_Intelligence.py"] = HEADER + '''
from mbsi.boundaries import detect_tissue_boundaries, compute_boundary_leakage, detect_invasion_corridors, detect_immune_exclusion_zones
require_reconstructed()
st.title("Boundary Intelligence")
if st.button("Analyze Boundaries"):
    r = st.session_state.reconstructed
    b = detect_tissue_boundaries(r)
    leak = compute_boundary_leakage(r, boundaries=b)
    excl = detect_immune_exclusion_zones(r, ["EPCAM"], ["CD3D"])
    inv = detect_invasion_corridors(r, ["EPCAM"], ["COL1A1"])
    st.session_state.boundaries_result = {"boundary_score": b["boundary_score"], "leakage": leak, "exclusion": excl, "invasion": inv}
if st.session_state.boundaries_result:
    st.metric("Leakage Score", f"{st.session_state.boundaries_result['leakage']:.4f}")
    st.line_chart(st.session_state.boundaries_result["boundary_score"][:50])
'''

pages["09_Communication_Physics.py"] = HEADER + '''
from mbsi.communication import compute_ligand_diffusion_field, compute_receptor_activation_flux, build_spatial_signaling_graph
require_reconstructed()
st.title("Communication Physics")
ligands = st.text_input("Ligands", "TGFB1,CXCL12,VEGFA").split(",")
receptors = st.text_input("Receptors", "TGFBR1,CXCR4,KDR").split(",")
if st.button("Compute Signaling"):
    r = st.session_state.reconstructed
    field = compute_ligand_diffusion_field(r, ligands)
    flux = compute_receptor_activation_flux(r, field, receptors)
    pairs = list(zip(ligands, receptors))
    graph = build_spatial_signaling_graph(r, pairs)
    st.session_state.communication_result = {"n_edges": graph.get("n_edges", 0), "flux_table": graph.get("flux_table", [])[:20]}
    st.success(f"Signaling graph: {graph.get('n_edges', 0)} edges")
if st.session_state.communication_result:
    st.dataframe(st.session_state.communication_result.get("flux_table", []))
'''

pages["10_Causal_Tissue_Model.py"] = HEADER + '''
from mbsi.causal import build_spatial_causal_dag, run_spatial_intervention, rank_causal_drivers
require_reconstructed()
causal_warning()
st.title("Causal Tissue Model")
target = st.text_input("Target node", "compartment")
outcome = st.text_input("Outcome node", "compartment")
if st.button("Build DAG & Intervene"):
    dag = build_spatial_causal_dag(st.session_state.reconstructed)
    result = run_spatial_intervention(dag, target, 0.0)
    drivers = rank_causal_drivers(dag, outcome)
    st.session_state.causal_result = {"nodes": list(dag.nodes()), "intervention": result, "drivers": drivers[:10]}
if st.session_state.causal_result:
    st.json(st.session_state.causal_result.get("drivers", []))
'''

pages["11_Temporal_Digital_Twin.py"] = HEADER + '''
from mbsi.temporal import simulate_tissue_future
from mbsi.digital_twin import build_tissue_digital_twin, simulate_treatment, compare_treatment_scenarios, TREATMENTS
require_reconstructed()
simulation_warning()
st.title("Temporal & Digital Twin")
treatment = st.selectbox("Treatment", list(TREATMENTS.keys()))
if st.button("Build Twin & Simulate"):
    twin = build_tissue_digital_twin(st.session_state.reconstructed)
    st.session_state.digital_twin = twin
    st.session_state.temporal_result = compare_treatment_scenarios(twin, [treatment, "untreated"])
if st.session_state.digital_twin:
    st.json(st.session_state.digital_twin)
if st.session_state.temporal_result:
    st.json(st.session_state.temporal_result)
'''

pages["12_Multimodal_Fusion.py"] = HEADER + '''
from mbsi.multimodal import build_multimodal_embedding, fuse_rna_image_protein
require_reconstructed()
st.title("Multimodal Fusion")
if st.button("Build Embedding"):
    r = fuse_rna_image_protein(st.session_state.reconstructed, protein=st.session_state.protein_data)
    emb = build_multimodal_embedding(r)
    st.session_state.multimodal_result = {"shape": emb.shape}
    st.session_state.reconstructed = r
    st.success(f"Embedding shape: {emb.shape}")
'''

pages["13_Validation_Benchmarking.py"] = HEADER + '''
from mbsi.validation import run_validation_suite
from mbsi.benchmarks.ablation import run_ablation_suite
require_reconstructed()
st.title("Validation & Benchmarking")
if st.button("Run Validation"):
    true = st.session_state.true_adata or st.session_state.ground_truth
    if true is None:
        st.error("Upload ground truth for validation")
    else:
        st.session_state.metrics = run_validation_suite(true, st.session_state.reconstructed, st.session_state.adata)
        st.session_state.analysis_state["metrics"] = st.session_state.metrics
        st.json(st.session_state.metrics)
'''

pages["14_AI_Tissue_Copilot.py"] = HEADER + '''
from mbsi.copilot import answer_tissue_query, QUERY_TEMPLATES, generate_biological_summary
st.title("AI Tissue Copilot")
st.caption("Answers from computed outputs only.")
for t in QUERY_TEMPLATES:
    if st.button(t, key=t):
        st.session_state.copilot_answer = answer_tissue_query(t, st.session_state.analysis_state or {"metrics": st.session_state.metrics})
query = st.text_input("Ask about your tissue analysis")
if st.button("Submit") and query:
    st.session_state.copilot_answer = answer_tissue_query(query, st.session_state.analysis_state or {"metrics": st.session_state.metrics, "boundaries": st.session_state.boundaries_result})
if "copilot_answer" in st.session_state:
    st.info(st.session_state.copilot_answer)
'''

pages["15_Export_Report.py"] = HEADER + '''
from app.components.report_builder import full_report_builder, generate_methods_text
from mbsi.copilot.report_text import generate_results_text
import json
from pathlib import Path
st.title("Export Report")
if st.session_state.reconstructed is not None:
    if st.button("Export h5ad"):
        out = Path("data/outputs/reconstructed.h5ad")
        out.parent.mkdir(parents=True, exist_ok=True)
        st.session_state.reconstructed.write_h5ad(out)
        st.success(f"Saved {out}")
    if st.button("Export metrics JSON") and st.session_state.metrics:
        Path("data/outputs/metrics.json").write_text(json.dumps(st.session_state.metrics, indent=2, default=str))
        st.success("Saved metrics.json")
    if st.session_state.metrics:
        st.download_button("Download results text", generate_results_text(st.session_state.metrics), "results.txt")
st.caption("Full HTML report and reproducibility bundle available via API POST /export/report")
'''

for name, content in pages.items():
    (PAGES / name).write_text(content)
print(f"Generated {len(pages)} pages")
