"""Xenium-specific QC metrics and filtering for Milestone 1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anndata as ad
import numpy as np
import pandas as pd

from mbsi.analysis.qc import compute_qc_metrics, flag_low_quality_spots, qc_summary_table
from mbsi.analysis.seurat_like.qc import filter_cells_or_spots


def _optional_artifact_paths(adata: ad.AnnData) -> Dict[str, str]:
    xenium_uns = adata.uns.get("xenium", {})
    return dict(xenium_uns.get("optional_artifacts", {}))


def _compute_transcript_density(adata: ad.AnnData, transcripts_path: Optional[str]) -> Tuple[ad.AnnData, bool]:
    """Add obs['transcript_density'] when transcripts table is available."""
    adata = adata.copy()
    if not transcripts_path or not Path(transcripts_path).is_file():
        adata.obs["transcript_density"] = np.nan
        adata.uns.setdefault("xenium_qc", {})["has_transcripts"] = False
        return adata, False

    try:
        path = Path(transcripts_path)
        if path.suffix == ".parquet":
            tx = pd.read_parquet(path, columns=None)
        else:
            tx = pd.read_csv(path)
        id_col = next((c for c in ("cell_id", "barcode", "Cell_ID") if c in tx.columns), None)
        if id_col is None:
            adata.obs["transcript_density"] = np.nan
            adata.uns.setdefault("xenium_qc", {})["has_transcripts"] = False
            return adata, False
        counts = tx.groupby(id_col).size()
        density = adata.obs_names.to_series().map(counts).fillna(0).astype(float).values
        adata.obs["transcript_density"] = density
        adata.uns.setdefault("xenium_qc", {})["has_transcripts"] = True
        return adata, True
    except Exception:
        adata.obs["transcript_density"] = np.nan
        adata.uns.setdefault("xenium_qc", {})["has_transcripts"] = False
        return adata, False


def _compute_spatial_coverage(adata: ad.AnnData) -> ad.AnnData:
    """Add spatial coverage metrics from obsm['spatial']."""
    adata = adata.copy()
    if "spatial" not in adata.obsm or adata.n_obs == 0:
        adata.uns.setdefault("xenium_qc", {})["spatial_coverage"] = 0.0
        return adata

    coords = np.asarray(adata.obsm["spatial"], dtype=float)
    x_span = float(coords[:, 0].max() - coords[:, 0].min()) + 1e-6
    y_span = float(coords[:, 1].max() - coords[:, 1].min()) + 1e-6
    area = x_span * y_span
    density = adata.n_obs / area
    adata.obs["spatial_bin"] = pd.cut(
        coords[:, 0],
        bins=min(10, max(2, adata.n_obs // 3)),
        labels=False,
        duplicates="drop",
    ).astype(float)
    adata.uns.setdefault("xenium_qc", {})["spatial_coverage"] = float(density)
    adata.uns["xenium_qc"]["spatial_area"] = float(area)
    return adata


def _set_segmentation_flags(adata: ad.AnnData, artifacts: Dict[str, str]) -> ad.AnnData:
    """Record boundary/morphology availability in uns and obs flags."""
    adata = adata.copy()
    has_boundaries = "boundaries" in artifacts and Path(artifacts["boundaries"]).is_file()
    has_morphology = "morphology" in artifacts and Path(artifacts["morphology"]).is_file()
    adata.uns.setdefault("xenium_qc", {})
    adata.uns["xenium_qc"]["has_cell_boundaries"] = has_boundaries
    adata.uns["xenium_qc"]["has_morphology"] = has_morphology
    adata.obs["has_boundaries"] = has_boundaries
    adata.obs["has_morphology"] = has_morphology
    return adata


def compute_xenium_qc_metrics(adata: ad.AnnData) -> ad.AnnData:
    """Compute standard + Xenium-specific QC metrics."""
    adata = compute_qc_metrics(adata)
    artifacts = _optional_artifact_paths(adata)
    adata, _ = _compute_transcript_density(adata, artifacts.get("transcripts"))
    adata = _compute_spatial_coverage(adata)
    adata = _set_segmentation_flags(adata, artifacts)
    return adata


def xenium_qc_summary(adata: ad.AnnData) -> pd.DataFrame:
    """Return QC summary table including Xenium-specific metrics."""
    summary = qc_summary_table(adata)
    extra_metrics = ["transcript_density", "spatial_bin"]
    rows = summary.to_dict("records")
    for metric in extra_metrics:
        if metric not in adata.obs.columns:
            continue
        s = adata.obs[metric].dropna()
        if s.empty:
            continue
        rows.append(
            {
                "metric": metric,
                "median": float(s.median()),
                "mean": float(s.mean()),
                "min": float(s.min()),
                "max": float(s.max()),
            }
        )
    xq = adata.uns.get("xenium_qc", {})
    for flag in ("has_transcripts", "has_cell_boundaries", "has_morphology"):
        rows.append({"metric": flag, "median": float(bool(xq.get(flag))), "mean": 0, "min": 0, "max": 0})
    if "spatial_coverage" in xq:
        rows.append(
            {
                "metric": "spatial_coverage",
                "median": float(xq["spatial_coverage"]),
                "mean": float(xq["spatial_coverage"]),
                "min": float(xq["spatial_coverage"]),
                "max": float(xq["spatial_coverage"]),
            }
        )
    return pd.DataFrame(rows)


def filter_genes_min_cells(adata: ad.AnnData, min_cells: int = 3) -> Tuple[ad.AnnData, int]:
    """Filter genes expressed in fewer than min_cells."""
    if min_cells <= 0 or adata.n_vars == 0:
        return adata, 0
    X = adata.X
    if hasattr(X, "toarray"):
        n_cells = np.asarray((X > 0).sum(axis=0)).flatten()
    else:
        n_cells = np.asarray((X > 0).sum(axis=0)).flatten()
    keep = n_cells >= min_cells
    removed = int((~keep).sum())
    if removed:
        adata = adata[:, keep].copy()
    return adata, removed


def run_xenium_qc(
    adata: ad.AnnData,
    min_counts: float = 10,
    min_genes: float = 5,
    max_mito: float = 50.0,
    min_cells_per_gene: int = 3,
    filter_tissue: bool = False,
) -> Tuple[ad.AnnData, pd.DataFrame, List[str]]:
    """Run Xenium QC: metrics, filter cells/genes, return (adata, summary, warnings)."""
    warnings: List[str] = []
    adata = adata.copy()
    if filter_tissue and "in_tissue" in adata.obs.columns:
        n_before = adata.n_obs
        adata = adata[adata.obs["in_tissue"].astype(bool)].copy()
        if adata.n_obs < n_before:
            warnings.append(f"Filtered {n_before - adata.n_obs} cells outside tissue.")

    adata = compute_xenium_qc_metrics(adata)
    adata = flag_low_quality_spots(adata, min_counts=min_counts, min_genes=min_genes, max_mito=max_mito)
    n_fail = int((~adata.obs["qc_pass"]).sum())
    if n_fail:
        warnings.append(f"{n_fail} cells failed QC thresholds.")
    adata = filter_cells_or_spots(adata)
    adata, n_removed = filter_genes_min_cells(adata, min_cells=min_cells_per_gene)
    if n_removed:
        warnings.append(f"Removed {n_removed} genes expressed in < {min_cells_per_gene} cells.")

    summary = xenium_qc_summary(adata)
    return adata, summary, warnings
