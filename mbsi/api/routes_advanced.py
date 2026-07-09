"""Extended API route handlers for advanced MBSI modules."""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import anndata as ad
import numpy as np
from fastapi import HTTPException
from fastapi.responses import FileResponse

from mbsi.api.job_store import InvalidJobIdError, OUTPUT_ROOT, get_job, job_exists, update_job, validate_job_id
from mbsi.segmentation import segment_tissue, segment_nuclei, infer_cell_boundaries, assign_spots_to_compartments
from mbsi.subcellular import infer_subcellular_compartments, partition_transcripts_by_compartment
from mbsi.subcellular.membrane_model import estimate_membrane_receptor_maps, estimate_secreted_ligand_fields
from mbsi.boundaries import detect_tissue_boundaries, compute_boundary_leakage, detect_invasion_corridors, detect_immune_exclusion_zones
from mbsi.communication import compute_ligand_diffusion_field, compute_receptor_activation_flux, build_spatial_signaling_graph
from mbsi.causal import build_spatial_causal_dag, run_spatial_intervention, rank_causal_drivers
from mbsi.temporal import align_spatial_timepoints, estimate_spatial_dynamics, simulate_tissue_future
from mbsi.digital_twin import build_tissue_digital_twin, simulate_treatment, compare_treatment_scenarios
from mbsi.multimodal import build_multimodal_embedding
from mbsi.copilot import answer_tissue_query, generate_biological_summary
from mbsi.copilot.report_text import generate_methods_text, generate_results_text
from mbsi.pipeline import run_full_pipeline


def _load_reconstructed(job_id: str) -> ad.AnnData:
    try:
        validate_job_id(job_id)
    except InvalidJobIdError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    job = get_job(job_id, load_adata=True, load_reconstructed=True)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if "reconstructed" in job:
        return job["reconstructed"]
    if "reconstructed_path" in job:
        return ad.read_h5ad(job["reconstructed_path"])
    raise HTTPException(status_code=400, detail="No reconstruction available")


def segment_endpoint(request: dict) -> Dict[str, Any]:
    job_id = request["job_id"]
    job = get_job(job_id, load_adata=True)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    adata = assign_spots_to_compartments(job["adata"])
    out_dir = Path("data/outputs") / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(out_dir / "segmented.h5ad")
    update_job(job_id, {"segmentation_path": str(out_dir / "segmented.h5ad")})
    return {"job_id": job_id, "n_compartments": len(adata.obs["compartment"].unique()), "status": "completed"}


def subcellular_endpoint(request: dict) -> Dict[str, Any]:
    recon = _load_reconstructed(request["job_id"])
    sub = infer_subcellular_compartments(recon)
    recon = partition_transcripts_by_compartment(recon, sub)
    return {"job_id": request["job_id"], "subcellular": {k: v.tolist() if hasattr(v, "tolist") else v for k, v in sub.items() if k != "note"}}


def boundaries_endpoint(request: dict) -> Dict[str, Any]:
    recon = _load_reconstructed(request["job_id"])
    b = detect_tissue_boundaries(recon)
    leak = compute_boundary_leakage(recon, boundaries=b)
    return {"job_id": request["job_id"], "leakage": leak, "mean_boundary": float(np.mean(b["boundary_score"]))}


def communication_endpoint(request: dict) -> Dict[str, Any]:
    recon = _load_reconstructed(request["job_id"])
    ligands = request.get("ligand_genes", ["TGFB1", "CXCL12"])
    receptors = request.get("receptor_genes", ["TGFBR1", "CXCR4"])
    field = compute_ligand_diffusion_field(recon, ligands)
    flux = compute_receptor_activation_flux(recon, field, receptors)
    pairs = list(zip(ligands[:len(receptors)], receptors))
    graph = build_spatial_signaling_graph(recon, [(l, r) for l, r in pairs if l in recon.var_names and r in recon.var_names])
    return {"job_id": request["job_id"], "n_edges": graph.get("n_edges", 0), "n_flux_entries": len(graph.get("flux_table", []))}


def causal_build_endpoint(request: dict) -> Dict[str, Any]:
    recon = _load_reconstructed(request["job_id"])
    dag = build_spatial_causal_dag(recon)
    return {"job_id": request["job_id"], "nodes": list(dag.nodes()), "n_edges": dag.number_of_edges()}


def causal_intervene_endpoint(request: dict) -> Dict[str, Any]:
    recon = _load_reconstructed(request["job_id"])
    dag = build_spatial_causal_dag(recon)
    target = request.get("target", list(dag.nodes())[0] if dag.nodes() else "compartment")
    result = run_spatial_intervention(dag, target, request.get("value", 0.0))
    return {"job_id": request["job_id"], **result}


def temporal_align_endpoint(request: dict) -> Dict[str, Any]:
    paths = request.get("timepoint_paths", [])
    adatas = [ad.read_h5ad(p) for p in paths]
    return align_spatial_timepoints(adatas)


def digital_twin_build_endpoint(request: dict) -> Dict[str, Any]:
    recon = _load_reconstructed(request["job_id"])
    twin = build_tissue_digital_twin(recon)
    update_job(request["job_id"], {"digital_twin": twin})
    return {"job_id": request["job_id"], "twin": twin}


def digital_twin_simulate_endpoint(request: dict) -> Dict[str, Any]:
    job = get_job(request["job_id"])
    twin = job.get("digital_twin") if job else None
    if not twin:
        recon = _load_reconstructed(request["job_id"])
        twin = build_tissue_digital_twin(recon)
    treatment = request.get("treatment", "PD-1 blockade")
    return simulate_treatment(twin, treatment)


def multimodal_fuse_endpoint(request: dict) -> Dict[str, Any]:
    recon = _load_reconstructed(request["job_id"])
    emb = build_multimodal_embedding(recon)
    return {"job_id": request["job_id"], "embedding_shape": list(emb.shape)}


def copilot_query_endpoint(request: dict) -> Dict[str, Any]:
    query = request.get("query", "")
    state = request.get("analysis_state", {})
    answer = answer_tissue_query(query, state)
    return {"query": query, "answer": answer}


def export_report_endpoint(request: dict) -> FileResponse:
    job_id = request["job_id"]
    try:
        safe_id = validate_job_id(job_id)
    except InvalidJobIdError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    out_dir = OUTPUT_ROOT / safe_id
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "report.html"
    metrics = request.get("metrics", {})
    html = f"<html><body><h1>MBSI Studio Report</h1><pre>{json.dumps(metrics, indent=2, default=str)}</pre></body></html>"
    report_path.write_text(html, encoding="utf-8")
    return FileResponse(str(report_path), filename=f"{job_id}_report.html")
