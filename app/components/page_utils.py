"""Shared Streamlit page utilities with demo fallbacks and system status."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

from mbsi.guardrails import GUARDRAIL_BANNER, CAUSAL_WARNING, SIMULATION_WARNING

DEMO_ADVANCED = Path("data/demo/advanced")
DEMO_BASIC = Path("data/demo")
OUTPUT_DIR = Path("data/outputs")


def init_session():
    """Initialize extended session state for MBSI Studio."""
    defaults = {
        "adata": None,
        "reconstructed": None,
        "true_adata": None,
        "metrics": {},
        "analysis_state": {},
        "spatial_demo": None,
        "recent_runs": [],
        "uploaded_image": None,
        "uploaded_segmentation": None,
        "ground_truth": None,
        "preprocessing_params": {},
        "analysis_results": None,
        "benchmark_results": None,
        "benchmark_leaderboard": None,
        "marker_table": None,
        "spatial_stats": None,
        "morphology_params": {},
        "segmentation_result": {},
        "tissue_mask": None,
        "nuclei_mask": None,
        "cell_mask": None,
        "cell_boundaries": None,
        "compartment_labels": None,
        "boundary_map": None,
        "segmentation_qc": None,
        "subcellular_result": {},
        "boundaries_result": {},
        "communication_result": {},
        "communication_results": None,
        "tme_results": None,
        "discovery_results": None,
        "ovarian_showcase_results": None,
        "causal_result": {},
        "temporal_result": {},
        "digital_twin": {},
        "multimodal_result": {},
        "ablation_results": None,
        "atac_data": None,
        "protein_data": None,
        "mutation_data": None,
        "clinical_data": None,
        "clinical_metadata": None,
        "project_metadata": {},
        "experimental_design": {},
        "platform_metadata": {},
        "project_completeness": 0,
        "dataset_readiness": 0,
        "dataset_compatibility": [],
        "using_synthetic_demo": False,
        "backend_online": None,
        "project_name": "No project loaded",
        "last_run": "",
        "demo_loaded": False,
        "active_module": "study_data",
        "selected_technology": "",
        "mbsi_platform": "",
        "mbsi_readiness": {},
        "ingestion_result": {},
        "download_manifest": None,
        "download_dir": None,
        "parsed_download_urls": [],
        "run_outputs": {},
        "figure_registry": {},
        "table_registry": {},
        "saas_warnings": [],
        "saas_findings": [],
        "findings": [],
        "evidence": [],
        "discovery_graph": None,
        "workflow_status": {},
        "job_status": {},
        "validators": {},
        "saas_notifications": [],
        "mbsi_settings": {},
        "sample_uploads": {},
        "sample_adatas": {},
        "sample_adata_paths": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def guardrail_banner():
    st.caption(GUARDRAIL_BANNER)


def causal_warning():
    st.warning(CAUSAL_WARNING)


def simulation_warning():
    st.warning(SIMULATION_WARNING)


def check_backend_online(timeout: float = 1.0) -> bool:
    """Check if FastAPI backend is reachable."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def demo_data_available() -> bool:
    return (DEMO_ADVANCED / "pseudo_visium_spots.h5ad").exists() or (
        DEMO_BASIC / "pseudo_visium_spots.h5ad"
    ).exists()


def load_advanced_demo_into_session(force: bool = False) -> bool:
    """Generate or load advanced spatial demo into session state."""
    if st.session_state.spatial_demo is not None and not force:
        return True
    try:
        from mbsi.demo.advanced_spatial_demo import generate_advanced_demo

        demo = generate_advanced_demo()
        st.session_state.spatial_demo = demo
        st.session_state.adata = demo["adata"]
        st.session_state.reconstructed = demo["reconstructed"]
        st.session_state.true_adata = demo["true_adata"]
        st.session_state.metrics = demo["metrics"]
        st.session_state.analysis_state = demo["analysis_state"]
        st.session_state.digital_twin = demo["digital_twin"]
        st.session_state.using_synthetic_demo = True
        st.session_state.demo_loaded = True
        st.session_state.last_run = "Advanced spatial demo"
        return True
    except Exception as exc:
        st.session_state._demo_error = str(exc)
        return False


def ensure_advanced_demo(show_info: bool = False) -> bool:
    """Ensure advanced demo is loaded; fallback to file-based or minimal demo."""
    if st.session_state.spatial_demo is not None:
        return True
    if load_advanced_demo_into_session():
        if show_info:
            st.info("Loaded advanced spatial demo.")
        return True
    if load_demo_into_session():
        if show_info:
            st.info("Loaded file-based demo dataset.")
        return True
    generate_synthetic_demo()
    if show_info:
        st.warning("Using minimal synthetic fallback.")
    return True


def load_demo_into_session(advanced: bool = True) -> bool:
    """Load demo h5ad files into session state. Returns True if loaded."""
    import anndata as ad

    paths = [DEMO_ADVANCED, DEMO_BASIC] if advanced else [DEMO_BASIC, DEMO_ADVANCED]
    for p in paths:
        spot_file = p / "pseudo_visium_spots.h5ad"
        if not spot_file.exists():
            continue
        st.session_state.adata = ad.read_h5ad(spot_file)
        true_file = p / "true_single_cell.h5ad"
        if true_file.exists():
            st.session_state.true_adata = ad.read_h5ad(true_file)
        recon_file = p / "reconstructed.h5ad"
        if recon_file.exists():
            st.session_state.reconstructed = ad.read_h5ad(recon_file)
        metrics_file = p / "metrics.json"
        if metrics_file.exists():
            st.session_state.metrics = json.loads(metrics_file.read_text())
        state_file = p / "analysis_state.json"
        if state_file.exists():
            st.session_state.analysis_state = json.loads(state_file.read_text())
        hist_file = p / "histology.png"
        if hist_file.exists() and st.session_state.spatial_demo is None:
            from PIL import Image
            import numpy as np
            img = np.array(Image.open(hist_file))
            st.session_state.spatial_demo = {"histology_image": img, "n_cells_total": st.session_state.reconstructed.n_obs if st.session_state.reconstructed else 0}
        st.session_state.using_synthetic_demo = False
        return True
    return False


def generate_synthetic_demo(n_spots: int = 120, n_genes: int = 300) -> None:
    """Create synthetic Visium-like spot data when no demo files exist."""
    from mbsi.analysis.demo import make_synthetic_visium_adata

    st.session_state.adata = make_synthetic_visium_adata(n_spots=n_spots, n_genes=n_genes, seed=42)
    st.session_state.using_synthetic_demo = True


def run_local_pipeline(quick: bool = True) -> None:
    """Run MBSI pipeline on current adata and update session."""
    from mbsi.reconstruction.solver import run_mbsi

    if st.session_state.adata is None:
        raise RuntimeError("No dataset loaded — upload real data first")
    st.session_state.reconstructed = run_mbsi(
        st.session_state.adata,
        n_cells_per_spot=3 if quick else 5,
        max_iter=50 if quick else 100,
        use_anisotropic=False,
        random_state=42,
    )
    save_reconstructed()
    st.session_state.last_run = "MBSI reconstruction"
    st.session_state.metrics = st.session_state.metrics or {"pipeline": "complete"}


def ensure_adata(show_warning: bool = True) -> bool:
    """Return True when real or explicitly loaded demo AnnData is in session."""
    if st.session_state.adata is not None:
        return True
    if show_warning:
        st.warning("No dataset loaded — upload spatial data in Study & Data, or use a labeled demo button.")
    return False


def ensure_reconstructed(show_warning: bool = True, quick: bool = False) -> bool:
    """Ensure reconstructed data exists; requires uploaded adata."""
    if st.session_state.reconstructed is not None:
        return True
    if st.session_state.adata is None:
        if show_warning:
            st.warning("Reconstruction unavailable — upload real data first.")
        return False
    try:
        run_local_pipeline(quick=quick or True)
        if show_warning:
            st.info("Generated reconstruction from uploaded data.")
        return True
    except Exception as exc:
        if show_warning:
            st.error(f"Could not run MBSI: {exc}")
        return False


def save_reconstructed(name: str = "reconstructed.h5ad") -> Path:
    """Save reconstructed AnnData to data/outputs/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    if st.session_state.reconstructed is not None:
        st.session_state.reconstructed.write_h5ad(path)
    return path


def save_metrics(name: str = "metrics.json") -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / name
    path.write_text(json.dumps(st.session_state.metrics, indent=2, default=str))
    return path


def require_adata():
    """Require uploaded data — no silent demo fallback."""
    if not ensure_adata():
        st.stop()


def require_reconstructed():
    """Require reconstruction from uploaded data."""
    if not ensure_reconstructed():
        st.stop()


def status_color(ok: bool, partial: bool = False) -> str:
    if ok:
        return "green"
    if partial:
        return "yellow"
    return "red"


def render_status_panel():
    """Render system status panel with green/yellow/red indicators."""
    backend = check_backend_online()
    st.session_state.backend_online = backend

    demo_ok = st.session_state.spatial_demo is not None or demo_data_available()
    try:
        from mbsi.reconstruction.solver import run_mbsi
        mbsi_ok = True
    except Exception:
        mbsi_ok = False
    try:
        from mbsi.segmentation import segment_tissue
        seg_ok = True
    except Exception:
        seg_ok = False
    try:
        from mbsi.validation import run_validation_suite
        val_ok = True
    except Exception:
        val_ok = False
    export_ok = OUTPUT_DIR.exists() or True

    items = [
        ("Backend", "online" if backend else "offline (local)", status_color(backend, partial=not backend)),
        ("Dataset bundle", "available" if demo_ok else "missing", status_color(demo_ok, partial=not demo_ok)),
        ("MBSI engine", "ready" if mbsi_ok else "error", status_color(mbsi_ok)),
        ("Segmentation", "ready" if seg_ok else "error", status_color(seg_ok)),
        ("Validation", "ready" if val_ok else "error", status_color(val_ok)),
        ("Export", "ready" if export_ok else "error", status_color(export_ok)),
    ]

    st.subheader("System Status")
    cols = st.columns(len(items))
    emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    for col, (label, detail, color) in zip(cols, items):
        with col:
            st.markdown(f"{emoji[color]} **{label}**")
            st.caption(detail)


def safe_import(module_path: str, fallback_msg: str):
    """Import optional module; show warning on failure."""
    try:
        parts = module_path.rsplit(".", 1)
        if len(parts) == 2:
            import importlib
            return importlib.import_module(module_path)
        return __import__(module_path)
    except Exception as exc:
        st.warning(f"{fallback_msg}: {exc}")
        return None


def has_real_adata() -> bool:
    """True when uploaded (non-demo) AnnData is in session."""
    return st.session_state.get("adata") is not None and not st.session_state.get("using_synthetic_demo", False)


def session_schema_snapshot() -> Dict[str, Any]:
    """Bridge Streamlit session state to schema objects."""
    from mbsi.schema.project import ProjectMetadata
    from mbsi.schema.sample import SampleRecord
    from mbsi.schema.study_design import StudyDesign
    from mbsi.schema.technology import get_technology

    project_meta = st.session_state.get("project_metadata") or {}
    project = ProjectMetadata.from_session(project_meta)
    project_id = project.title or st.session_state.get("project_name", "")
    design = StudyDesign.from_session(
        st.session_state.get("experimental_design"),
        project_id=project_id,
    )
    samples_raw = st.session_state.get("sample_metadata")
    if hasattr(samples_raw, "to_dict"):
        samples_raw = samples_raw.to_dict("records")
    samples = SampleRecord.from_rows(samples_raw or [])
    tech_key = st.session_state.get("selected_technology") or st.session_state.get("mbsi_platform", "")
    tech = get_technology(tech_key)
    return {
        "project": project,
        "study_design": design,
        "samples": samples,
        "technology_key": tech_key,
        "technology_spec": tech.to_dict() if tech else {},
        "project_id": project_id,
    }
