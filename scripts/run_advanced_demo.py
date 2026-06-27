"""
Advanced synthetic demo for MBSI Studio v2.

Generates 500 cells, 100 spots, 300 genes with compartments,
boundaries, ligand-receptor pairs, and runs full pipeline.
"""

import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from mbsi.benchmarks.pseudo_visium import make_pseudo_visium
from mbsi.pipeline import run_full_pipeline

COMPARTMENTS = ["tumor", "stroma", "immune", "necrosis"]
MARKER_GENES = {
    "tumor": ["EPCAM", "KRT8", "MKI67"],
    "stroma": ["COL1A1", "DCN", "FAP"],
    "immune": ["CD3D", "CD8A", "CD68"],
    "necrosis": ["HIF1A", "BNIP3"],
}
LIGAND_RECEPTOR = [("TGFB1", "TGFBR1"), ("CXCL12", "CXCR4"), ("VEGFA", "KDR")]


def generate_advanced_dataset(
    n_cells: int = 500,
    n_spots: int = 100,
    n_genes: int = 300,
    random_state: int = 42,
):
    np.random.seed(random_state)
    gene_names = []
    for comp, markers in MARKER_GENES.items():
        gene_names.extend(markers)
    for lr in LIGAND_RECEPTOR:
        gene_names.extend(lr)
    while len(gene_names) < n_genes:
        gene_names.append(f"GENE_{len(gene_names)}")
    gene_names = gene_names[:n_genes]

    coords = np.zeros((n_cells, 2))
    labels = np.zeros(n_cells, dtype=int)
    per_comp = n_cells // 4
    centers = [(50, 50), (150, 50), (50, 150), (150, 150)]
    for c in range(4):
        s, e = c * per_comp, (c + 1) * per_comp if c < 3 else n_cells
        cx, cy = centers[c]
        coords[s:e] = np.column_stack([
            cx + np.random.randn(e - s) * 15,
            cy + np.random.randn(e - s) * 15,
        ])
        labels[s:e] = c

    X = np.random.poisson(2, (n_cells, n_genes)).astype(np.float32)
    for c, comp in enumerate(COMPARTMENTS):
        mask = labels == c
        for mg in MARKER_GENES[comp]:
            if mg in gene_names:
                gi = gene_names.index(mg)
                X[mask, gi] += np.random.poisson(8, mask.sum())

    # Ligand-receptor co-expression
    for lig, rec in LIGAND_RECEPTOR:
        if lig in gene_names and rec in gene_names:
            li, ri = gene_names.index(lig), gene_names.index(rec)
            tumor_mask = labels == 0
            X[tumor_mask, li] += np.random.poisson(5, tumor_mask.sum())
            stroma_mask = labels == 1
            X[stroma_mask, ri] += np.random.poisson(4, stroma_mask.sum())

    true_adata = ad.AnnData(X=X)
    true_adata.var_names = gene_names
    true_adata.obs_names = [f"cell_{i}" for i in range(n_cells)]
    true_adata.obsm["spatial"] = coords
    true_adata.obs["compartment"] = [COMPARTMENTS[l] for l in labels]
    true_adata.obs["label"] = labels
    true_adata.obs["cell_type"] = true_adata.obs["compartment"]

    spot_adata = make_pseudo_visium(
        true_adata,
        spot_diameter=55.0,
        aggregation="hex",
        n_spots=n_spots,
        random_state=random_state,
    )
    return true_adata, spot_adata


def run_advanced_demo(output_dir: str = "data/demo/advanced", random_state: int = 42):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    print("Generating advanced demo dataset...")
    true_adata, spot_adata = generate_advanced_dataset(random_state=random_state)
    true_adata.write_h5ad(out / "true_single_cell.h5ad")
    spot_adata.write_h5ad(out / "pseudo_visium_spots.h5ad")

    print("Running full pipeline...")
    state = run_full_pipeline(
        spot_adata,
        true_adata=true_adata,
        n_cells_per_spot=5,
        use_anisotropic=False,
        random_state=random_state,
    )
    state["reconstructed"].write_h5ad(out / "reconstructed.h5ad")

    metrics = state.get("metrics") or {}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, default=str))

    serializable = {
        k: v for k, v in state.items()
        if k not in ("spot_adata", "reconstructed", "true_adata", "ligand_field", "receptor_flux", "invasion_corridors")
    }
    serializable["n_cells"] = state["reconstructed"].n_obs
    serializable["leakage_score"] = state.get("leakage_score")
    serializable["boundaries"] = {
        "mean_boundary_score": state["boundaries"].get("mean_boundary_score"),
        "note": state["boundaries"].get("note"),
    }
    serializable["immune_exclusion"] = {"mean": state["immune_exclusion"]["mean"]}
    serializable["compartments"] = state["compartments"]
    serializable["metrics"] = metrics
    (out / "analysis_state.json").write_text(json.dumps(serializable, indent=2, default=str))

    print(f"Advanced demo saved to {out}")
    return state


if __name__ == "__main__":
    run_advanced_demo()
