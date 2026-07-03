"""Full pipeline orchestration."""

from typing import Any, Dict, Optional

import anndata as ad
import numpy as np

from mbsi.analysis.svg import detect_svgs
from mbsi.reconstruction.solver import run_mbsi
from mbsi.segmentation.compartments import infer_compartment_labels
from mbsi.segmentation.masks import voronoi_cell_regions
from mbsi.subcellular.compartments import infer_subcellular_compartments
from mbsi.subcellular.transcript_partition import partition_transcripts_by_compartment
from mbsi.boundaries.detect import detect_tissue_boundaries
from mbsi.boundaries.leakage import compute_boundary_leakage
from mbsi.boundaries.invasion import detect_immune_exclusion_zones, detect_invasion_corridors
from mbsi.communication.ligand_diffusion import compute_ligand_diffusion_field
from mbsi.communication.receptor_flux import compute_receptor_activation_flux
from mbsi.communication.signaling_graph import build_spatial_signaling_graph
from mbsi.causal.dag import build_spatial_causal_dag
from mbsi.causal.interventions import run_spatial_intervention
from mbsi.digital_twin.state import build_tissue_digital_twin
from mbsi.digital_twin.simulate import simulate_treatment, compare_treatment_scenarios
from mbsi.multimodal.fusion import build_multimodal_embedding
from mbsi.foundation.embeddings import compute_tissue_embedding
from mbsi.validation import run_validation_suite


DEFAULT_LIGAND_RECEPTOR_PAIRS = [
    ("TGFB1", "TGFBR1"),
    ("CXCL12", "CXCR4"),
    ("VEGFA", "KDR"),
]


def run_full_pipeline(
    spot_adata: ad.AnnData,
    true_adata: Optional[ad.AnnData] = None,
    image: Optional[np.ndarray] = None,
    ligand_genes: Optional[list] = None,
    receptor_genes: Optional[list] = None,
    tumor_markers: Optional[list] = None,
    immune_markers: Optional[list] = None,
    random_state: int = 42,
    svg_n_top: int = 2000,
    svg_k: int = 6,
    svg_n_perms: int = 0,
    svg_fdr_alpha: float = 0.05,
    **mbsi_kwargs,
) -> Dict[str, Any]:
    """Run complete MBSI Studio pipeline and return analysis state."""
    ligand_genes = ligand_genes or ["TGFB1", "CXCL12", "VEGFA"]
    receptor_genes = receptor_genes or ["TGFBR1", "CXCR4", "KDR"]
    tumor_markers = tumor_markers or ["EPCAM", "KRT8"]
    immune_markers = immune_markers or ["CD3D", "CD8A"]

    spot_adata = infer_compartment_labels(spot_adata)
    reconstructed = run_mbsi(spot_adata, image=image, random_state=random_state, **mbsi_kwargs)
    reconstructed = infer_compartment_labels(reconstructed)

    subcell = infer_subcellular_compartments(reconstructed, image=image)
    reconstructed = partition_transcripts_by_compartment(reconstructed, subcell)

    # Spatially variable genes with significance testing (Moran's I + BH-FDR).
    # Run on the reconstructed field; fall back gracefully if spatial coords
    # or a suitable expression layer are unavailable.
    try:
        svg_layer = "logcounts" if "logcounts" in reconstructed.layers else None
        svg_table = detect_svgs(
            reconstructed,
            layer=svg_layer if svg_layer is not None else "X",
            n_top=svg_n_top,
            k=svg_k,
            method="moran",
            n_perms=svg_n_perms,
            fdr_alpha=svg_fdr_alpha,
            random_state=random_state,
        )
    except Exception as exc:  # pragma: no cover - defensive: never break pipeline
        svg_table = None
        svg_error = str(exc)
    else:
        svg_error = None

    boundaries = detect_tissue_boundaries(reconstructed)
    leakage = compute_boundary_leakage(reconstructed, boundaries=boundaries)
    immune_excl = detect_immune_exclusion_zones(reconstructed, tumor_markers, immune_markers)
    invasion = detect_invasion_corridors(reconstructed, tumor_markers, ["COL1A1"])

    ligand_field = compute_ligand_diffusion_field(reconstructed, ligand_genes)
    receptor_flux = compute_receptor_activation_flux(reconstructed, ligand_field, receptor_genes)
    pairs = [(l, r) for l, r in DEFAULT_LIGAND_RECEPTOR_PAIRS if l in reconstructed.var_names and r in reconstructed.var_names]
    signaling = build_spatial_signaling_graph(reconstructed, pairs) if pairs else {"flux_table": [], "n_edges": 0}

    dag = build_spatial_causal_dag(reconstructed)
    intervention = run_spatial_intervention(dag, target=list(dag.nodes())[0] if dag.nodes() else "compartment", value=0.0)

    twin = build_tissue_digital_twin(reconstructed)
    treatment_sim = compare_treatment_scenarios(twin, ["untreated", "PD-1 blockade", "cisplatin"])

    embedding = compute_tissue_embedding(reconstructed)
    reconstructed.obsm["X_mbsi"] = embedding

    metrics = None
    if true_adata is not None:
        metrics = run_validation_suite(true_adata, reconstructed, spot_adata)

    state = {
        "spot_adata": spot_adata,
        "reconstructed": reconstructed,
        "true_adata": true_adata,
        "subcellular": subcell,
        "boundaries": {**boundaries, "mean_boundary_score": float(np.mean(boundaries["boundary_score"]))},
        "leakage_score": leakage,
        "immune_exclusion": {"mean": float(np.mean(immune_excl)), "scores": immune_excl},
        "invasion_corridors": invasion,
        "ligand_field": ligand_field,
        "receptor_flux": receptor_flux,
        "signaling": signaling,
        "causal_dag_nodes": list(dag.nodes()),
        "intervention": intervention,
        "digital_twin": twin,
        "treatment_simulation": treatment_sim["scenarios"],
        "metrics": metrics,
        "n_cells": reconstructed.n_obs,
        "compartments": {"labels": list(reconstructed.obs["compartment"].unique())},
        "embedding_shape": embedding.shape,
        "svg_table": svg_table,
        "svg_n_significant": (
            int(svg_table["is_svg"].sum())
            if svg_table is not None and "is_svg" in svg_table.columns
            else None
        ),
        "svg_error": svg_error,
    }
    return state
