"""Deterministic synthetic dashboard demo data (seed=42)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import ndimage
from skimage.measure import find_contours

CELL_TYPE_COLORS = {
    "Tumor Epithelial": "#ff4f7b",
    "Cancer Stem-like": "#f7c948",
    "CAF (myCAFs)": "#4cd964",
    "CAF (iCAFs)": "#ff9f1a",
    "Endothelial": "#30d5c8",
    "T cells": "#3b82f6",
    "B cells": "#c084fc",
    "Macrophages": "#f97316",
    "Plasma cells": "#ec4899",
    "Mast cells": "#a855f7",
    "Other": "#b8c1cc",
}

CELL_COUNTS = {
    "Tumor Epithelial": 9642,
    "Cancer Stem-like": 2118,
    "CAF (myCAFs)": 3127,
    "CAF (iCAFs)": 2034,
    "Endothelial": 1836,
    "T cells": 2986,
    "B cells": 1224,
    "Macrophages": 1987,
    "Plasma cells": 876,
    "Mast cells": 654,
    "Other": 1260,
}

COMPOSITION_PCT = {
    "Tumor Epithelial": 34.6,
    "Cancer Stem-like": 7.6,
    "CAF (myCAFs)": 11.2,
    "CAF (iCAFs)": 7.3,
    "Endothelial": 6.6,
    "T cells": 10.7,
    "B cells": 4.4,
    "Macrophages": 7.1,
    "Plasma cells": 3.1,
    "Mast cells": 2.3,
    "Other": 5.1,
}


def _generate_he_image(width: int = 900, height: int = 700, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y, x = np.ogrid[:height, :width]
    base = np.stack([
        rng.normal(215, 20, (height, width)),
        rng.normal(165, 25, (height, width)),
        rng.normal(180, 22, (height, width)),
    ], axis=-1).astype(np.float32)

    nests = [(0.42, 0.45, 0.16), (0.58, 0.38, 0.11), (0.35, 0.58, 0.09), (0.62, 0.62, 0.08)]
    for tx, ty, r in nests:
        dist = np.sqrt(((x - tx * width) / (r * width)) ** 2 + ((y - ty * height) / (r * height)) ** 2)
        nest = np.clip(1.0 - dist, 0, 1) ** 1.4
        base[..., 0] -= nest * 50
        base[..., 2] -= nest * 35

    noise = rng.normal(0, 8, (height, width))
    base += noise[..., None]
    base = ndimage.gaussian_filter(base, sigma=1.2)
    return np.clip(base, 0, 255).astype(np.uint8)


def _build_tissue_regions(width: int = 900, height: int = 700, seed: int = 42) -> Dict[str, np.ndarray]:
    """Synthetic tissue compartment masks for boundary extraction."""
    rng = np.random.default_rng(seed + 7)
    y, x = np.ogrid[:height, :width]
    tumor = np.zeros((height, width), dtype=np.float32)
    for tx, ty, r in [(0.42, 0.45, 0.16), (0.58, 0.38, 0.11), (0.35, 0.58, 0.09)]:
        dist = np.sqrt(((x - tx * width) / (r * width)) ** 2 + ((y - ty * height) / (r * height)) ** 2)
        tumor = np.maximum(tumor, np.clip(1.0 - dist, 0, 1))

    stroma_band = ndimage.gaussian_filter(
        np.clip(1.0 - ndimage.distance_transform_edt(tumor > 0.35) / 80.0, 0, 1),
        sigma=6,
    )
    necrotic = ndimage.gaussian_filter(
        np.exp(-((x - 0.48 * width) ** 2 + (y - 0.52 * height) ** 2) / (0.04 * width) ** 2),
        sigma=4,
    )
    immune = ndimage.gaussian_filter(
        np.exp(-((x - 0.62 * width) ** 2 + (y - 0.62 * height) ** 2) / (0.06 * width) ** 2),
        sigma=3,
    )
    vessel = ndimage.gaussian_filter(
        np.exp(-((x - 0.28 * width) ** 2 + (y - 0.35 * height) ** 2) / (0.03 * width) ** 2),
        sigma=2,
    )
    noise = rng.normal(0, 0.04, (height, width))
    region_maps = {
        "tumor": tumor,
        "stroma": stroma_band,
        "necrotic": necrotic,
        "immune": immune,
        "vessel": vessel,
    }
    for key, arr in region_maps.items():
        region_maps[key] = np.clip(arr + noise * 0.15, 0, 1).astype(np.float32)
    return region_maps


def _contour_from_mask(
    mask: np.ndarray,
    width: int,
    height: int,
    n_points: int = 80,
    level: float = 0.45,
) -> Tuple[List[float], List[float]]:
    """Extract a smooth irregular contour in normalized 0–1 coordinates."""
    contours = find_contours(mask, level=level * float(mask.max() or 1.0))
    if not contours:
        return [], []
    verts = max(contours, key=len)
    if len(verts) < 4:
        return [], []

    step = max(1, len(verts) // n_points)
    sampled = verts[::step]
    xs = (sampled[:, 1] / width).tolist()
    ys = (sampled[:, 0] / height).tolist()
    return xs, ys


def _assign_cell_positions(n_visible: int, extent: float, seed: int) -> tuple[np.ndarray, np.ndarray, list]:
    rng = np.random.default_rng(seed + 1)
    types = list(CELL_COUNTS.keys())
    weights = np.array([CELL_COUNTS[t] for t in types], dtype=float)
    weights /= weights.sum()
    type_idx = rng.choice(len(types), size=n_visible, p=weights)

    centers = [(0.42, 0.45), (0.58, 0.38), (0.35, 0.58), (0.62, 0.62), (0.48, 0.52)]
    xs, ys, labels = [], [], []
    for i in range(n_visible):
        c = centers[type_idx[i] % len(centers)]
        xs.append((c[0] + rng.normal(0, 0.08)) * extent)
        ys.append((c[1] + rng.normal(0, 0.08)) * extent)
        labels.append(types[type_idx[i]])
    return np.array(xs), np.array(ys), labels


def generate_dashboard_demo(seed: int = 42) -> Dict[str, Any]:
    """Generate all synthetic data for the reference dashboard."""
    rng = np.random.default_rng(seed)
    extent = 1000.0
    n_visible = 6500

    histology = _generate_he_image(seed=seed)
    regions = _build_tissue_regions(seed=seed)
    xs, ys, labels = _assign_cell_positions(n_visible, extent, seed)

    cells = pd.DataFrame({
        "x": xs, "y": ys, "cell_type": labels,
        "color": [CELL_TYPE_COLORS[l] for l in labels],
    })

    cell_types = pd.DataFrame([
        {"name": k, "color": v, "count": CELL_COUNTS[k], "pct": COMPOSITION_PCT[k]}
        for k, v in CELL_TYPE_COLORS.items()
    ])

    pathways = pd.DataFrame([
        {"pathway": "CXCL12–CXCR4", "probability": 0.93},
        {"pathway": "CCL5–CCR5", "probability": 0.87},
        {"pathway": "MIF–CD74/CD44", "probability": 0.81},
        {"pathway": "TGFB1–TGFBR1/2", "probability": 0.76},
        {"pathway": "PD-L1–PD-1", "probability": 0.71},
        {"pathway": "VEGFA–VEGFR2", "probability": 0.69},
        {"pathway": "SPP1–CD44", "probability": 0.65},
        {"pathway": "IL6–IL6R", "probability": 0.61},
        {"pathway": "IFNG–IFNGR1/2", "probability": 0.56},
        {"pathway": "ANGPT2–TIE2", "probability": 0.52},
    ])

    interactions = pd.DataFrame([
        {"niche": "CAF (myCAF)", "target": "Tumor", "score": 0.92},
        {"niche": "Macrophage", "target": "T cell", "score": 0.84},
        {"niche": "Endothelial", "target": "T cell", "score": 0.78},
        {"niche": "Tumor", "target": "CAF (iCAF)", "score": 0.71},
        {"niche": "B cell", "target": "T cell", "score": 0.66},
        {"niche": "Plasma", "target": "B cell", "score": 0.58},
    ])

    causal = pd.DataFrame([
        {"driver": "TGFB Signaling", "effect": 0.81},
        {"driver": "CAF Activation", "effect": 0.78},
        {"driver": "Hypoxia", "effect": 0.71},
        {"driver": "EMT Program", "effect": 0.69},
        {"driver": "Angiogenesis", "effect": 0.61},
        {"driver": "Immune Suppression", "effect": 0.59},
        {"driver": "Matrix Remodeling", "effect": 0.54},
    ])

    composition = pd.DataFrame([
        {"cell_type": k, "pct": v} for k, v in COMPOSITION_PCT.items()
    ])

    traj_x = rng.normal(0, 1, 400)
    traj_y = rng.normal(0, 1, 400)
    traj_pt = rng.uniform(0, 1, 400)
    trajectory = pd.DataFrame({"x": traj_x, "y": traj_y, "pseudotime": traj_pt})

    marker_genes = ["EPCAM", "CD8A", "MKI67", "COL1A1", "PECAM1", "CD68"]
    marker_maps = {}
    for g in marker_genes:
        field = rng.uniform(0, 1, (80, 80))
        field = ndimage.gaussian_filter(field, sigma=2)
        marker_maps[g] = field

    ligand_field = ndimage.gaussian_filter(rng.uniform(0, 1, (80, 80)), sigma=3)
    invasion_field = ndimage.gaussian_filter(rng.uniform(0, 0.5, (80, 80)), sigma=2)

    treatment = {
        "Cisplatin": {"Tumor Kill": 0.72, "CAF Activity": 0.45, "Immune Infiltration": 0.55,
                      "Angiogenesis": 0.40, "EMT": 0.35, "Resistance Score": 0.62},
        "PARP inhibitor": {"Tumor Kill": 0.65, "CAF Activity": 0.50, "Immune Infiltration": 0.48,
                           "Angiogenesis": 0.42, "EMT": 0.38, "Resistance Score": 0.58},
        "PD-1 blockade": {"Tumor Kill": 0.48, "CAF Activity": 0.55, "Immune Infiltration": 0.82,
                          "Angiogenesis": 0.50, "EMT": 0.42, "Resistance Score": 0.45},
        "CAR-T placeholder": {"Tumor Kill": 0.78, "CAF Activity": 0.52, "Immune Infiltration": 0.88,
                              "Angiogenesis": 0.46, "EMT": 0.40, "Resistance Score": 0.50},
    }
    baseline = {"Tumor Kill": 0.35, "CAF Activity": 0.60, "Immune Infiltration": 0.40,
                "Angiogenesis": 0.55, "EMT": 0.50, "Resistance Score": 0.70}

    # Network graph nodes
    n_nodes = 45
    net_labels = rng.choice(list(CELL_TYPE_COLORS.keys())[:7], size=n_nodes)
    net_x = rng.uniform(0, 1, n_nodes)
    net_y = rng.uniform(0, 1, n_nodes)
    network_nodes = pd.DataFrame({
        "id": range(n_nodes), "x": net_x, "y": net_y,
        "cell_type": net_labels,
        "color": [CELL_TYPE_COLORS.get(l, "#b8c1cc") for l in net_labels],
    })
    edges = []
    for i in range(n_nodes):
        for j in rng.choice(n_nodes, size=2, replace=False):
            if i != j:
                edges.append((i, j))
    network_edges = pd.DataFrame(edges, columns=["source", "target"])

    h, w = histology.shape[:2]
    tumor_x, tumor_y = _contour_from_mask(regions["tumor"], w, h, n_points=90, level=0.42)
    stroma_x, stroma_y = _contour_from_mask(regions["stroma"], w, h, n_points=70, level=0.55)
    boundaries: List[Dict] = []
    if tumor_x:
        boundaries.append({"x": tumor_x, "y": tumor_y, "color": "#f7c948", "label": "Tumor–Stroma"})
    if stroma_x:
        boundaries.append({"x": stroma_x, "y": stroma_y, "color": "#30d5c8", "label": "Stroma Interface"})
    if not boundaries:
        boundaries = [
            {"x0": 0.32, "y0": 0.30, "x1": 0.58, "y1": 0.55},
            {"x0": 0.52, "y0": 0.35, "x1": 0.72, "y1": 0.62},
        ]

    return {
        "histology_image": histology,
        "tissue_regions": regions,
        "cells": cells,
        "cell_types": cell_types,
        "pathways": pathways,
        "interactions": interactions,
        "causal": causal,
        "composition": composition,
        "trajectory": trajectory,
        "treatment": treatment,
        "baseline": baseline,
        "marker_maps": marker_maps,
        "ligand_field": ligand_field,
        "invasion_field": invasion_field,
        "network_nodes": network_nodes,
        "network_edges": network_edges,
        "boundaries": boundaries,
        "tissue_extent": extent,
        "summary": {
            "spots": 5184,
            "genes": 18432,
            "cells": 27842,
            "cell_types_n": 23,
            "resolution_um": 0.25,
            "boundary_leakage": 0.91,
            "morans_i": 0.88,
            "tissue_area_mm2": 11.2,
        },
    }
