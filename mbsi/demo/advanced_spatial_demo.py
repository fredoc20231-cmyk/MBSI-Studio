"""
Advanced spatial biology demo data for MBSI Studio cockpit UI.

Generates synthetic H&E histology, ~27k cells, neighborhood graphs,
ligand-receptor pathways, marker maps, pseudotime, invasion, causal ranking,
and digital-twin treatment scores.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anndata as ad
import networkx as nx
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage
from skimage import filters, morphology

from mbsi.benchmarks.pseudo_visium import make_pseudo_visium

CELL_TYPES: List[Dict[str, str]] = [
    {"name": "Tumor epithelial", "color": "#ff5c7a", "compartment": "tumor"},
    {"name": "CAF", "color": "#ffb020", "compartment": "stroma"},
    {"name": "CD8 T cell", "color": "#39d98a", "compartment": "immune"},
    {"name": "CD4 T cell", "color": "#4f7cff", "compartment": "immune"},
    {"name": "Macrophage", "color": "#9b6cff", "compartment": "immune"},
    {"name": "B cell", "color": "#00c2cb", "compartment": "immune"},
    {"name": "Endothelial", "color": "#e879f9", "compartment": "stroma"},
    {"name": "NK cell", "color": "#a3e635", "compartment": "immune"},
    {"name": "Necrotic", "color": "#64748b", "compartment": "necrosis"},
    {"name": "Stem-like", "color": "#f472b6", "compartment": "tumor"},
]

MARKER_GENES = {
    "EPCAM": "Tumor epithelial",
    "CD8A": "CD8 T cell",
    "CD3D": "CD4 T cell",
    "CD68": "Macrophage",
    "COL1A1": "CAF",
    "PECAM1": "Endothelial",
    "MKI67": "Stem-like",
    "TGFB1": "CAF",
    "CXCL12": "CAF",
    "VEGFA": "Endothelial",
}

LR_PAIRS = [
    ("TGFB1", "TGFBR1", "TGF-β signaling"),
    ("CXCL12", "CXCR4", "Chemokine axis"),
    ("VEGFA", "KDR", "Angiogenesis"),
    ("CD274", "PDCD1", "Immune checkpoint"),
    ("CCL5", "CCR5", "T cell recruitment"),
    ("WNT5A", "FZD5", "Wnt pathway"),
]


def _generate_he_image(width: int = 1024, height: int = 1024, seed: int = 42) -> np.ndarray:
    """Procedural H&E-like tissue image with tumor nests, stroma, necrosis, immune niches."""
    rng = np.random.default_rng(seed)
    y, x = np.ogrid[:height, :width]
    cx, cy = width * 0.45, height * 0.48

    # Base eosin (pink) stroma
    base = np.stack([
        rng.normal(220, 18, (height, width)),
        rng.normal(170, 22, (height, width)),
        rng.normal(185, 20, (height, width)),
    ], axis=-1).astype(np.float32)

    # Tumor nests — dense hematoxylin regions
    for i, (tx, ty, r) in enumerate([
        (0.42, 0.45, 0.18), (0.55, 0.38, 0.12), (0.35, 0.55, 0.10),
    ]):
        dist = np.sqrt(((x - tx * width) / (r * width)) ** 2 + ((y - ty * height) / (r * height)) ** 2)
        nest = np.clip(1.0 - dist, 0, 1) ** 1.5
        base[..., 0] -= nest * 45
        base[..., 1] -= nest * 35
        base[..., 2] += nest * 25

    # Necrosis — pale avascular zones
    nec = np.exp(-(((x - 0.72 * width) ** 2 + (y - 0.65 * height) ** 2) / (0.08 * width) ** 2))
    base += nec[..., None] * np.array([35, 30, 25])

    # Immune niche — slightly basophilic infiltrate
    immune = np.exp(-(((x - 0.28 * width) ** 2 + (y - 0.35 * height) ** 2) / (0.06 * width) ** 2))
    base[..., 2] += immune * 30
    base[..., 0] -= immune * 15

    # Nuclei texture (hematoxylin speckle)
    noise = rng.normal(0, 1, (height, width))
    nuclei = filters.gaussian(noise, sigma=1.2) < -0.35
    nuclei = morphology.binary_dilation(nuclei, morphology.disk(1))
    base[nuclei, 0] -= 40
    base[nuclei, 1] -= 30
    base[nuclei, 2] += 35

    # Vessel-like structures
    vessels = filters.sobel(rng.normal(0, 1, (height, width)))
    vessels = filters.gaussian(vessels, sigma=2) > 0.4
    base[vessels, 0] += 20
    base[vessels, 1] += 10

    base = ndimage.gaussian_filter(base, sigma=0.8)
    return np.clip(base, 0, 255).astype(np.uint8)


def _assign_cell_positions(n_cells: int, width: float, height: float, rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray]:
    """Place cells in tissue regions matching histology compartments."""
    type_probs = np.array([0.22, 0.14, 0.10, 0.08, 0.09, 0.05, 0.07, 0.04, 0.06, 0.15])
    type_probs /= type_probs.sum()
    type_idx = rng.choice(len(CELL_TYPES), size=n_cells, p=type_probs)

    coords = np.zeros((n_cells, 2))
    for i, ct in enumerate(CELL_TYPES):
        mask = type_idx == i
        n = mask.sum()
        if n == 0:
            continue
        comp = ct["compartment"]
        if comp == "tumor":
            cx, cy, spread = width * 0.45, height * 0.45, 0.22
        elif comp == "stroma":
            cx, cy, spread = width * 0.50, height * 0.52, 0.35
        elif comp == "immune":
            cx, cy, spread = width * 0.28, height * 0.35, 0.12
        else:  # necrosis
            cx, cy, spread = width * 0.72, height * 0.65, 0.10
        coords[mask, 0] = rng.normal(cx, width * spread, n)
        coords[mask, 1] = rng.normal(cy, height * spread, n)

    coords[:, 0] = np.clip(coords[:, 0], 5, width - 5)
    coords[:, 1] = np.clip(coords[:, 1], 5, height - 5)
    return coords, type_idx


def _build_neighborhood_graph(coords: np.ndarray, k: int = 8, max_edges: int = 8000) -> nx.Graph:
    """k-NN neighborhood graph on cell coordinates."""
    from sklearn.neighbors import NearestNeighbors

    n = min(len(coords), 6000)
    idx = np.linspace(0, len(coords) - 1, n, dtype=int)
    sub = coords[idx]
    nn = NearestNeighbors(n_neighbors=min(k + 1, n)).fit(sub)
    dists, indices = nn.kneighbors(sub)

    g = nx.Graph()
    edge_count = 0
    for i in range(n):
        g.add_node(int(idx[i]))
        for j, d in zip(indices[i][1:], dists[i][1:], strict=False):
            if edge_count >= max_edges:
                break
            u, v = int(idx[i]), int(idx[j])
            if not g.has_edge(u, v):
                g.add_edge(u, v, weight=float(1.0 / (1.0 + d)))
                edge_count += 1
    return g


def generate_advanced_demo(
    n_cells: int = 27000,
    n_spots: int = 900,
    n_genes: int = 300,
    plot_subset: int = 5000,
    image_size: int = 1024,
    tissue_extent: float = 1000.0,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Generate comprehensive synthetic spatial biology demo bundle.

    Returns
    -------
    dict
        Keys: histology_image, cells, cell_types, n_cells_total, plot_indices,
        neighborhood_graph, lr_pathways, marker_maps, pseudotime, boundary_leakage,
        invasion_heatmap, causal_drivers, digital_twin, treatment_radar,
        adata, reconstructed, true_adata, metrics, analysis_state.
    """
    rng = np.random.default_rng(random_state)
    np.random.seed(random_state)

    histology = _generate_he_image(image_size, image_size, seed=random_state)
    scale = tissue_extent / image_size

    coords, type_idx = _assign_cell_positions(n_cells, tissue_extent, tissue_extent, rng)
    cell_type_names = [CELL_TYPES[i]["name"] for i in type_idx]
    compartments = [CELL_TYPES[i]["compartment"] for i in type_idx]

    # Pseudotime along tumor-stroma axis
    pseudotime = (coords[:, 0] / tissue_extent + rng.normal(0, 0.05, n_cells))
    pseudotime = (pseudotime - pseudotime.min()) / (pseudotime.max() - pseudotime.min() + 1e-8)

    gene_names = list(MARKER_GENES.keys())
    while len(gene_names) < n_genes:
        gene_names.append(f"GENE_{len(gene_names)}")
    gene_names = gene_names[:n_genes]

    X = rng.poisson(2, (n_cells, n_genes)).astype(np.float32)
    for gene, ctype in MARKER_GENES.items():
        if gene in gene_names:
            gi = gene_names.index(gene)
            mask = np.array([ct == ctype for ct in cell_type_names])
            X[mask, gi] += rng.poisson(10, mask.sum())

    true_adata = ad.AnnData(X=X)
    true_adata.var_names = gene_names
    true_adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
    true_adata.obsm["spatial"] = coords
    true_adata.obs["cell_type"] = cell_type_names
    true_adata.obs["compartment"] = compartments
    true_adata.obs["pseudotime"] = pseudotime

    spot_adata = make_pseudo_visium(
        true_adata,
        spot_diameter=55.0,
        aggregation="hex",
        n_spots=n_spots,
        random_state=random_state,
    )

    # Lightweight reconstructed subset for MBSI compatibility (full 27k is heavy)
    recon_n = min(2500, n_cells)
    recon_idx = rng.choice(n_cells, recon_n, replace=False)
    reconstructed = true_adata[recon_idx].copy()

    # Marker expression maps (on plot subset)
    plot_indices = rng.choice(n_cells, min(plot_subset, n_cells), replace=False)
    plot_coords = coords[plot_indices]
    plot_types = [cell_type_names[i] for i in plot_indices]

    marker_maps = {}
    for gene in list(MARKER_GENES.keys())[:6]:
        if gene in gene_names:
            gi = gene_names.index(gene)
            marker_maps[gene] = X[plot_indices, gi].astype(np.float32)

    # L-R pathway scores
    lr_rows = []
    for lig, rec, pathway in LR_PAIRS:
        li = gene_names.index(lig) if lig in gene_names else None
        ri = gene_names.index(rec) if rec in gene_names else None
        lig_expr = float(X[:, li].mean()) if li is not None else rng.uniform(0.5, 2.0)
        rec_expr = float(X[:, ri].mean()) if ri is not None else rng.uniform(0.5, 2.0)
        score = float(np.sqrt(lig_expr * rec_expr) * rng.uniform(0.6, 1.4))
        lr_rows.append({
            "pathway": pathway,
            "ligand": lig,
            "receptor": rec,
            "lr_score": round(score, 3),
            "flux": round(score * rng.uniform(0.3, 0.9), 3),
            "direction": rng.choice(["tumor→stroma", "stroma→immune", "immune→tumor"]),
        })
    lr_pathways = pd.DataFrame(lr_rows)

    # Ligand gradient heatmap (2D field)
    gx = np.linspace(0, tissue_extent, 40)
    gy = np.linspace(0, tissue_extent, 40)
    xx, yy = np.meshgrid(gx, gy)
    ligand_field = np.exp(-((xx - tissue_extent * 0.45) ** 2 + (yy - tissue_extent * 0.45) ** 2) / (200 ** 2))
    ligand_field += 0.3 * np.exp(-((xx - tissue_extent * 0.28) ** 2 + (yy - tissue_extent * 0.35) ** 2) / (120 ** 2))
    ligand_field = ligand_field / ligand_field.max()

    # Neighborhood graph
    neighborhood_graph = _build_neighborhood_graph(coords)

    # Boundary leakage + invasion heatmap
    boundary_leakage = float(rng.uniform(0.08, 0.22))
    inv_grid = np.zeros((30, 30))
    inv_grid[10:20, 8:14] = rng.uniform(0.4, 0.9, (10, 6))
    inv_grid[12:18, 18:26] = rng.uniform(0.3, 0.7, (6, 8))
    invasion_heatmap = inv_grid

    # Causal drivers
    causal_genes = ["TGFB1", "COL1A1", "MKI67", "CD8A", "VEGFA", "CXCL12", "EPCAM", "FAP"]
    causal_drivers = [
        {"gene": g, "score": float(rng.uniform(0.35, 0.98)), "effect": rng.choice(["pro-tumor", "anti-tumor", "immune-mod"]) }
        for g in causal_genes
    ]
    causal_drivers.sort(key=lambda x: -x["score"])

    # Digital twin + treatment radar
    treatments = ["Untreated", "Anti-PD-1", "Chemotherapy", "TGF-β blockade", "Combo"]
    treatment_radar = {
        "categories": ["Tumor burden", "Immune infiltration", "Stromal barrier", "Vascularity", "Resistance"],
        "series": {},
    }
    for t in treatments:
        treatment_radar["series"][t] = [float(rng.uniform(0.2, 0.95)) for _ in treatment_radar["categories"]]

    comp_names = sorted({ct["compartment"] for ct in CELL_TYPES})
    digital_twin = {
        "n_cells": n_cells,
        "compartments": {
            comp: round(sum(1 for c in compartments if c == comp) / n_cells, 3)
            for comp in comp_names
        },
        "immune_infiltration": round(sum(1 for c in compartments if c == "immune") / n_cells, 3),
        "resistance_score": float(rng.uniform(0.15, 0.45)),
        "treatment_radar": treatment_radar,
    }

    # Cell composition for donut chart
    composition = {}
    for ct in CELL_TYPES:
        composition[ct["name"]] = int(sum(1 for n in cell_type_names if n == ct["name"]))

    cells_df = pd.DataFrame({
        "x": plot_coords[:, 0],
        "y": plot_coords[:, 1],
        "cell_type": plot_types,
        "compartment": [compartments[i] for i in plot_indices],
        "pseudotime": pseudotime[plot_indices],
        "cell_id": plot_indices,
    })

    metrics = {
        "pearson_correlation": float(rng.uniform(0.72, 0.89)),
        "spearman_correlation": float(rng.uniform(0.68, 0.85)),
        "rmse": float(rng.uniform(0.08, 0.18)),
        "boundary_leakage": boundary_leakage,
        "n_cells": n_cells,
        "n_spots": n_spots,
    }

    analysis_state = {
        "leakage_score": boundary_leakage,
        "compartments": digital_twin["compartments"],
        "immune_exclusion": {"mean": float(rng.uniform(0.02, 0.08))},
        "causal_drivers": causal_drivers,
        "digital_twin": digital_twin,
        "treatment_simulation": {t: {"resistance_score_change": float(rng.uniform(-0.2, 0.1))} for t in treatments},
    }

    return {
        "histology_image": histology,
        "histology_pil": Image.fromarray(histology),
        "cells": cells_df,
        "cell_types": CELL_TYPES,
        "n_cells_total": n_cells,
        "n_spots": n_spots,
        "plot_indices": plot_indices,
        "neighborhood_graph": neighborhood_graph,
        "lr_pathways": lr_pathways,
        "ligand_field": ligand_field,
        "marker_maps": marker_maps,
        "pseudotime": pseudotime[plot_indices],
        "boundary_leakage": boundary_leakage,
        "invasion_heatmap": invasion_heatmap,
        "causal_drivers": causal_drivers,
        "digital_twin": digital_twin,
        "treatment_radar": treatment_radar,
        "composition": composition,
        "adata": spot_adata,
        "reconstructed": reconstructed,
        "true_adata": true_adata,
        "metrics": metrics,
        "analysis_state": analysis_state,
        "tissue_extent": tissue_extent,
    }


def save_advanced_demo(output_dir: str | Path = "data/demo/advanced", **kwargs) -> Dict[str, Any]:
    """Generate and persist demo bundle to disk."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    demo = generate_advanced_demo(**kwargs)
    demo["true_adata"].write_h5ad(out / "true_single_cell.h5ad")
    demo["adata"].write_h5ad(out / "pseudo_visium_spots.h5ad")
    demo["reconstructed"].write_h5ad(out / "reconstructed.h5ad")
    (out / "metrics.json").write_text(json.dumps(demo["metrics"], indent=2))
    (out / "analysis_state.json").write_text(json.dumps(demo["analysis_state"], indent=2, default=str))
    demo["histology_pil"].save(out / "histology.png")
    return demo
