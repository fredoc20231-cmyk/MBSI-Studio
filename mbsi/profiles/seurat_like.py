"""Seurat-like workflow presets for MBSI analysis."""

from __future__ import annotations

from typing import Any, Dict, List

WORKFLOW_PRESETS: Dict[str, Dict[str, Any]] = {
    "basic_unsupervised": {
        "label": "Basic unsupervised",
        "description": "QC → log-normalize → HVG → PCA → neighbors → Leiden → UMAP → markers",
        "normalization": "log1p",
        "n_top_genes": 2000,
        "n_comps": 30,
        "n_neighbors": 30,
        "n_pcs": 15,
        "resolution": 1.0,
        "clustering": "Leiden",
    },
    "sctransform_like": {
        "label": "SCTransform-like",
        "description": "Pearson residuals or scvi/scanpy SCTransform fallback → PCA → clustering",
        "normalization": "sctransform_like",
        "n_top_genes": 3000,
        "n_comps": 50,
        "n_neighbors": 30,
        "n_pcs": 30,
        "resolution": 0.8,
        "clustering": "Leiden",
    },
    "spatial_transcriptomics": {
        "label": "Spatial transcriptomics",
        "description": "QC → normalize → spatial-aware clustering → SVGs → spatial DE",
        "normalization": "log1p",
        "n_top_genes": 2000,
        "n_comps": 30,
        "n_neighbors": 30,
        "n_pcs": 15,
        "resolution": 1.0,
        "clustering": "Spatial graph",
        "spatial_stats": True,
    },
    "multimodal_wnn": {
        "label": "Multimodal WNN",
        "description": "RNA + protein/ATAC → separate reductions → weighted nearest neighbors",
        "normalization": "log1p",
        "modalities": ["rna", "protein"],
        "wnn": True,
        "n_top_genes": 2000,
        "resolution": 0.8,
    },
    "reference_mapping": {
        "label": "Reference mapping",
        "description": "Map query to reference atlas via label transfer",
        "normalization": "log1p",
        "reference_required": True,
        "n_top_genes": 2000,
    },
    "scrna_scatac_integration": {
        "label": "scRNA/scATAC integration",
        "description": "Bridge integration or concat-PCA fallback for RNA+ATAC",
        "modalities": ["rna", "atac"],
        "integration": "bridge",
        "n_top_genes": 2000,
    },
    "visium_hd": {
        "label": "Visium HD",
        "description": "Bin-level QC → normalization → cell-segmentation assisted clustering",
        "normalization": "log1p",
        "resolution_class": "high",
        "n_top_genes": 3000,
        "n_neighbors": 50,
        "resolution": 1.2,
    },
    "imaging_based_spatial": {
        "label": "Imaging-based spatial",
        "description": "Xenium/CosMx/CODEX cell-level workflow",
        "normalization": "log1p",
        "segmentation_assisted": True,
        "n_top_genes": 1500,
        "resolution": 0.6,
    },
    "large_scale_sketch": {
        "label": "Large-scale sketch",
        "description": "Sketch subset → PCA/cluster → project to full dataset",
        "normalization": "log1p",
        "sketch": True,
        "sketch_n": 50000,
        "backed": True,
        "n_top_genes": 2000,
    },
}


def list_workflow_presets() -> List[str]:
    return list(WORKFLOW_PRESETS.keys())


def get_workflow_preset(key: str) -> Dict[str, Any]:
    if key not in WORKFLOW_PRESETS:
        key = "basic_unsupervised"
    preset = dict(WORKFLOW_PRESETS[key])
    preset["key"] = key
    return preset
