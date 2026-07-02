# Milestone 1: Visium, Xenium & Generic Real Data

**Scope:** Only **10x Visium**, **10x Xenium**, and **Generic h5ad/CSV** are functional in Milestone 1. All other platforms appear in the catalog as **Coming later** and must not be shown as supported workflows.

## Functional pipeline

Study Setup → upload/download → technology detection → readiness → QC → filtering → normalization → PCA/UMAP → clustering → markers → spatial viz → squidpy neighborhood enrichment → Moran's I → export h5ad/CSV/report

| Stage | Module / API | Notes |
|-------|----------------|-------|
| Study Setup | `study_data` | Technology selector (3 active platforms) |
| Upload / download | `POST /api/dataset/upload`, Study & Data UI | `technology_hint=visium\|xenium\|generic_h5ad` |
| Technology detection | `mbsi.io.detect`, ingest | Auto-detect from bundle layout |
| Readiness | `GET /api/dataset/readiness`, validators | Score + missing fields |
| QC & filtering | `qc_transformation`, `POST /api/workflow/run` | Spot/cell filters, mito threshold |
| Normalization | QC workspace, preprocess workflow | log1p / SCTransform-like |
| PCA / UMAP | Visualization, analyze workflow | Scanpy reductions |
| Clustering | Leiden / Louvain | `obs['cluster']` |
| Markers | Seurat-like pipeline | Rank genes per cluster |
| Spatial viz | Visualization workspace | Spatial feature, quilt, UMAP |
| Squidpy nhood enrichment | Xenium/Visium pipeline (optional) | When `squidpy` installed + clusters present |
| Moran's I | `spatial_variable_genes` | Spatial autocorrelation table |
| Export | `report_export` | h5ad, CSV bundle, HTML report |

## Supported technologies (Milestone 1)

| Key | Label | Required files |
|-----|-------|----------------|
| `visium` | 10x Visium | `filtered_feature_bc_matrix.h5` or MTX trio; `spatial/tissue_positions_list.csv` |
| `xenium` | 10x Xenium | `cell_feature_matrix.h5`; `cells.csv.gz` or `cells.parquet` |
| `generic_h5ad` | Generic AnnData / CSV | `.h5ad` with `obsm['spatial']`, or CSV matrix + coordinates |

### Xenium optional files

- `transcripts.parquet`
- `cell_boundaries.parquet`
- Morphology image (e.g. `morphology.ome.tif`)

### Coming later (not functional)

Visium HD, MERFISH/MERSCOPE, CosMx, Stereo-seq, CODEX, Slide-seq, Spatial ATAC — catalog entries only; UI shows gray **Coming later** label; compatibility matrix status `coming_later`.

## Acceptance checklist

### Visium (Space Ranger)

- [x] Detect `filtered_feature_bc_matrix.h5` or MTX trio
- [x] Detect `spatial/tissue_positions_list.csv`
- [x] Detect `spatial/scalefactors_json.json`
- [x] Optional tissue image
- [x] AnnData with `obsm['spatial']`, `obs.in_tissue`, `uns.spatial`
- [x] Readiness score ≥ 50 on valid bundle
- [x] Full Milestone 1 analysis chain + report export

### Xenium

- [x] Detect `cell_feature_matrix.h5`
- [x] Detect `cells.csv.gz` or `cells.parquet`
- [x] Optional transcripts, boundaries, morphology (path references)
- [x] Cell-level AnnData with spatial centroids
- [x] UI file checklist in Study & Data when Xenium selected
- [x] Same analysis chain as Visium
- [x] Xenium QC module (`mbsi/analysis/xenium_qc.py`): transcript density, spatial coverage, boundary flags
- [x] Full pipeline test: `tests/test_xenium_qc_pipeline.py`

### Generic h5ad / CSV

- [x] `.h5ad` with expression + spatial coords
- [x] CSV matrix + `coordinates.csv` with x/y columns
- [x] Routed via `ingest_dataset(..., technology_hint="generic_h5ad")`

## API (Milestone 1)

See `docs/MBSI_API_MILESTONE1.md` for endpoint details.

## Pipeline orchestrator

Milestone 1 end-to-end analysis: `mbsi/workflows/xenium_pipeline.py`

- `run_xenium_milestone_pipeline(adata, output_dir)` — Xenium QC + shared analysis chain
- `run_visium_milestone_pipeline(adata, output_dir)` — Visium QC + same chain

Outputs: `processed.h5ad`, `cluster_labels.csv`, `cell_type_annotations.csv`, `cluster_markers.csv`, `qc_summary.csv`, `spatial_autocorrelation.csv`, spatial HTML plots, HTML report, `pipeline_manifest.json`.

## Smoke tests

```bash
PYTHONPATH=. python scripts/smoke_test_launch_imports.py
PYTHONPATH=. pytest tests/test_visium_ingestion.py tests/test_xenium_ingestion.py tests/test_xenium_qc_pipeline.py tests/test_real_data_workflow.py tests/test_ingest_universal.py -q
```

## Out of scope

MERFISH, CosMx, Stereo-seq, CODEX, Spatial ATAC, Visium HD, benchmark hub, discovery intelligence (beyond stubs), foundation models.

## Stubbed / deferred

- Full `cell_boundaries.parquet` geometry parse (QC flags only)
- Full `transcripts.parquet` layer load (per-cell density when path available)
- Morphology OME-TIFF raster load
- **SpatialData** — optional `spatialdata` install; AnnData fallback with warning
- **squidpy** spatial_neighbors / nhood_enrichment — optional; skipped when not installed
- Legacy platform loaders return honest stubs via `ingest_dataset`
