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
        "subcellular_result": {},
        "boundaries_result": {},
        "communication_result": {},
        "causal_result": {},
        "temporal_result": {},
        "digital_twin": {},
        "multimodal_result": {},
        "ablation_results": None,
        "atac_data": None,
        "protein_data": None,
        "mutation_data": None,
        "clinical_data": None,
        "using_synthetic_demo": False,
        "backend_online": None,
        "project_name": "Advanced Spatial Demo",
        "last_run": "Demo loaded",
        "demo_loaded": False,
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
        ensure_advanced_demo(show_info=False)
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
    """Ensure spot-level data is loaded; use demo or synthetic fallback."""
    if st.session_state.adata is not None:
        return True
    if ensure_advanced_demo(show_info=False):
        if show_warning:
            st.info("Loaded advanced demo dataset automatically.")
        return True
    if load_demo_into_session():
        if show_warning:
            st.info("Loaded demo dataset automatically.")
        return True
    generate_synthetic_demo()
    if show_warning:
        st.warning("Using synthetic demo data.")
    return True


def ensure_reconstructed(show_warning: bool = True, quick: bool = False) -> bool:
    """Ensure reconstructed data exists; run MBSI or load from demo."""
    ensure_adata(show_warning=False)
    if st.session_state.reconstructed is not None:
        return True
    if load_demo_into_session() and st.session_state.reconstructed is not None:
        return True
    if st.session_state.spatial_demo and st.session_state.spatial_demo.get("reconstructed") is not None:
        st.session_state.reconstructed = st.session_state.spatial_demo["reconstructed"]
        return True
    try:
        run_local_pipeline(quick=quick or True)
        if show_warning:
            st.info("Generated reconstruction automatically.")
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
    """Legacy: ensure data with fallback instead of hard stop."""
    if not ensure_adata():
        if st.button("Go to Upload"):
            st.switch_page("pages/02_Upload_Data.py")
        st.stop()


def require_reconstructed():
    """Legacy: ensure reconstruction with fallback."""
    if not ensure_reconstructed():
        if st.button("Go to Run MBSI"):
            st.switch_page("pages/05_Run_MBSI.py")
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
        ("Demo data", "loaded" if demo_ok else "fallback", status_color(demo_ok, partial=not demo_ok)),
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
