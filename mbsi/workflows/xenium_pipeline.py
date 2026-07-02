"""Milestone 1 Visium/Xenium end-to-end analysis orchestrator."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import anndata as ad
import pandas as pd

from mbsi.analysis.markers import rank_cluster_markers, top_markers_per_cluster
from mbsi.analysis.seurat_like import run_seurat_like_pipeline
from mbsi.analysis.xenium_qc import run_xenium_qc, xenium_qc_summary
from mbsi.phenotyping import score_marker_panel
from mbsi.reports.final_report import generate_final_html_report
from mbsi.spatial_stats import spatial_autocorrelation_table


def export_markers_csv(markers: pd.DataFrame, path: Path) -> Path:
    """Write cluster marker table to CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    markers.to_csv(path, index=False)
    return path


def _run_optional_squidpy(adata: ad.AnnData) -> Dict[str, Any]:
    """Run squidpy spatial_neighbors + nhood_enrichment when available."""
    result: Dict[str, Any] = {"available": False, "warnings": []}
    try:
        import squidpy as sq
    except ImportError:
        result["warnings"].append("squidpy not installed — skipping spatial neighborhood enrichment.")
        return result

    if "spatial" not in adata.obsm or "cluster" not in adata.obs.columns:
        result["warnings"].append("Missing spatial coords or cluster labels for squidpy.")
        return result

    try:
        sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=6)
        enrichment = sq.gr.nhood_enrichment(adata, cluster_key="cluster")
        result["available"] = True
        result["nhood_enrichment"] = enrichment
    except Exception as exc:
        result["warnings"].append(f"squidpy analysis skipped: {exc}")
    return result


def _spatial_plot_paths(adata: ad.AnnData, out_dir: Path) -> List[str]:
    """Save spatial scatter HTML plots for clusters and total counts."""
    paths: List[str] = []
    if "spatial" not in adata.obsm:
        return paths

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        import plotly.express as px

        coords = adata.obsm["spatial"]
        df = pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1]})
        if "cluster" in adata.obs.columns:
            df["cluster"] = adata.obs["cluster"].astype(str).values
            fig = px.scatter(df, x="x", y="y", color="cluster", title="Spatial clusters")
            cluster_path = out_dir / "spatial_clusters.html"
            fig.write_html(str(cluster_path))
            paths.append(str(cluster_path))
        if "total_counts" in adata.obs.columns:
            df["total_counts"] = adata.obs["total_counts"].values
            fig = px.scatter(df, x="x", y="y", color="total_counts", title="Spatial total counts")
            counts_path = out_dir / "spatial_total_counts.html"
            fig.write_html(str(counts_path))
            paths.append(str(counts_path))
    except Exception as exc:
        warnings.warn(f"Spatial plot export skipped: {exc}")
    return paths


def _cell_type_annotations(adata: ad.AnnData) -> pd.DataFrame:
    """Build cell type table from phenotyping scores or cluster labels."""
    rows = {"cell_id": adata.obs_names.astype(str)}
    if "cluster" in adata.obs.columns:
        rows["cluster"] = adata.obs["cluster"].astype(str).values
        rows["cell_type"] = [f"cluster_{c}" for c in rows["cluster"]]
    else:
        rows["cluster"] = ["unassigned"] * adata.n_obs
        rows["cell_type"] = ["unassigned"] * adata.n_obs

    panel_cols = [c for c in adata.obs.columns if c.startswith("panel_")]
    for col in panel_cols[:3]:
        rows[col] = adata.obs[col].values
    return pd.DataFrame(rows)


def _export_milestone_outputs(
    adata: ad.AnnData,
    results: Dict[str, Any],
    output_dir: Path,
    *,
    platform: str,
    qc_summary: pd.DataFrame,
    spatial_stats: pd.DataFrame,
    squidpy_result: Dict[str, Any],
    spatial_plots: List[str],
    report_path: Optional[Path] = None,
) -> Dict[str, str]:
    """Write processed h5ad, CSVs, parameters, and optional HTML report."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    h5ad_path = output_dir / "processed.h5ad"
    adata.write_h5ad(h5ad_path)

    cluster_csv = output_dir / "cluster_labels.csv"
    pd.DataFrame(
        {"cell_id": adata.obs_names.astype(str), "cluster": adata.obs.get("cluster", "unassigned")}
    ).to_csv(cluster_csv, index=False)

    annotations = _cell_type_annotations(adata)
    annotations_csv = output_dir / "cell_type_annotations.csv"
    annotations.to_csv(annotations_csv, index=False)

    markers = results.get("markers", pd.DataFrame())
    markers_csv = output_dir / "cluster_markers.csv"
    if isinstance(markers, pd.DataFrame) and not markers.empty:
        export_markers_csv(markers, markers_csv)
    else:
        pd.DataFrame(columns=["cluster", "gene", "score"]).to_csv(markers_csv, index=False)

    qc_summary.to_csv(output_dir / "qc_summary.csv", index=False)
    spatial_stats.to_csv(output_dir / "spatial_autocorrelation.csv", index=False)

    manifest = {
        "platform": platform,
        "n_obs": adata.n_obs,
        "n_vars": adata.n_vars,
        "n_clusters": int(adata.obs["cluster"].nunique()) if "cluster" in adata.obs.columns else 0,
        "spatial_plots": spatial_plots,
        "squidpy_available": squidpy_result.get("available", False),
        "squidpy_warnings": squidpy_result.get("warnings", []),
        "parameters": results.get("parameters", {}),
    }
    (output_dir / "pipeline_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))

    outputs = {
        "processed_h5ad": str(h5ad_path),
        "cluster_labels_csv": str(cluster_csv),
        "cell_type_annotations_csv": str(annotations_csv),
        "cluster_markers_csv": str(markers_csv),
        "qc_summary_csv": str(output_dir / "qc_summary.csv"),
        "spatial_autocorrelation_csv": str(output_dir / "spatial_autocorrelation.csv"),
        "manifest_json": str(output_dir / "pipeline_manifest.json"),
    }
    if report_path:
        outputs["report_html"] = str(report_path)
    for i, plot in enumerate(spatial_plots):
        outputs[f"spatial_plot_{i}"] = plot
    return outputs


def _run_milestone_pipeline(
    adata: ad.AnnData,
    output_dir: Path,
    *,
    platform: str,
    min_counts: float = 10,
    min_genes: float = 5,
    max_mito: float = 50.0,
    min_cells_per_gene: int = 3,
    filter_tissue: bool = False,
    n_top_genes: Optional[int] = None,
    resolution: Optional[float] = None,
    spatial_stats_top_n: int = 50,
    run_phenotyping: bool = True,
    generate_report: bool = True,
) -> Dict[str, Any]:
    """Shared Milestone 1 pipeline for Visium and Xenium."""
    output_dir = Path(output_dir)
    all_warnings: List[str] = []

    if platform == "xenium":
        adata, qc_summary, qc_warnings = run_xenium_qc(
            adata,
            min_counts=min_counts,
            min_genes=min_genes,
            max_mito=max_mito,
            min_cells_per_gene=min_cells_per_gene,
            filter_tissue=filter_tissue,
        )
    else:
        from mbsi.analysis.seurat_like.qc import run_qc

        adata, qc_summary, qc_warnings = run_qc(
            adata,
            min_counts=min_counts,
            min_genes=min_genes,
            max_mito=max_mito,
            filter_tissue=filter_tissue,
        )
        if min_cells_per_gene > 0:
            from mbsi.analysis.xenium_qc import filter_genes_min_cells

            adata, n_removed = filter_genes_min_cells(adata, min_cells=min_cells_per_gene)
            if n_removed:
                qc_warnings.append(f"Removed {n_removed} genes expressed in < {min_cells_per_gene} cells.")
    all_warnings.extend(qc_warnings)

    preset_kwargs: Dict[str, Any] = {
        "preset": "spatial_transcriptomics",
        "min_counts": 0,
        "min_genes": 0,
        "max_mito": 100.0,
        "filter_tissue": False,
    }
    if n_top_genes is not None:
        preset_kwargs["n_top_genes"] = n_top_genes
    if resolution is not None:
        preset_kwargs["resolution"] = resolution

    results = run_seurat_like_pipeline(adata, **preset_kwargs)
    all_warnings.extend(results.get("warnings", []))
    adata = results["adata"]

    if run_phenotyping:
        try:
            adata, _ = score_marker_panel(adata, "immune")
        except Exception as exc:
            all_warnings.append(f"Phenotyping stub skipped: {exc}")

    spatial_stats = spatial_autocorrelation_table(adata, n_top=spatial_stats_top_n, k=4)
    squidpy_result = _run_optional_squidpy(adata)
    all_warnings.extend(squidpy_result.get("warnings", []))
    spatial_plots = _spatial_plot_paths(adata, output_dir)

    report_path = None
    if generate_report:
        snapshot = {
            "mbsi_platform": platform,
            "analysis_results": {
                "n_obs": adata.n_obs,
                "n_clusters": adata.obs["cluster"].nunique() if "cluster" in adata.obs.columns else 0,
            },
            "marker_table": results.get("markers"),
            "spatial_stats": spatial_stats,
            "using_synthetic_demo": False,
            "registered": {"figures": [], "tables": [], "findings": []},
            "notebook": [],
        }
        report_path = generate_final_html_report(output_dir / "reports", snapshot=snapshot)

    if platform == "xenium":
        qc_summary = xenium_qc_summary(adata)

    output_paths = _export_milestone_outputs(
        adata,
        results,
        output_dir,
        platform=platform,
        qc_summary=qc_summary,
        spatial_stats=spatial_stats,
        squidpy_result=squidpy_result,
        spatial_plots=spatial_plots,
        report_path=report_path,
    )

    return {
        "adata": adata,
        "qc_summary": qc_summary,
        "markers": results.get("markers"),
        "spatial_stats": spatial_stats,
        "squidpy": squidpy_result,
        "spatial_plots": spatial_plots,
        "output_paths": output_paths,
        "warnings": all_warnings,
        "platform": platform,
    }


def run_xenium_milestone_pipeline(
    adata: ad.AnnData,
    output_dir: Path,
    **params: Any,
) -> Dict[str, Any]:
    """Run full Milestone 1 Xenium pipeline and export outputs."""
    return _run_milestone_pipeline(
        adata,
        output_dir,
        platform="xenium",
        filter_tissue=params.pop("filter_tissue", False),
        **params,
    )


def run_visium_milestone_pipeline(
    adata: ad.AnnData,
    output_dir: Path,
    **params: Any,
) -> Dict[str, Any]:
    """Run full Milestone 1 Visium pipeline and export outputs."""
    return _run_milestone_pipeline(
        adata,
        output_dir,
        platform="visium",
        filter_tissue=params.pop("filter_tissue", True),
        **params,
    )
