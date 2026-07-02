# Milestone 1: Visium & Xenium Real Data

Scope: **10x Visium**, **10x Xenium**, and **generic h5ad/CSV** fallback only.

## Workflow

Study Setup → Ingestion → Readiness → QC → Normalization → Visualization → Clustering → Marker genes → SVG → Spatial domains → Basic phenotyping → Report export

## Acceptance checklist

### Visium (Space Ranger)

- [x] Detect `filtered_feature_bc_matrix.h5` or `filtered_feature_bc_matrix/` MTX trio
- [x] Detect `spatial/tissue_positions_list.csv` (or `tissue_positions.csv`)
- [x] Detect `spatial/scalefactors_json.json`
- [x] Optional tissue image (`tissue_hires_image.png` / `tissue_lowres_image.png`)
- [x] AnnData with `obsm['spatial']`, `obs.in_tissue`, `uns.spatial`
- [x] Readiness score ≥ 50 on valid bundle
- [x] QC & Transformation workspace runs on uploaded data
- [x] Spatial plot data available in Visualization
- [x] Normalize → PCA → UMAP → Leiden clustering
- [x] Marker gene table produced
- [x] SVG (Moran's I) table produced
- [x] Spatial domains assigned
- [x] HTML report export succeeds

### Xenium

- [x] Detect `cell_feature_matrix.h5`
- [x] Detect `cells.csv.gz` or `cells.parquet`
- [x] Optional: `transcripts.parquet`, `cell_boundaries.parquet`, `morphology.ome.tif`
- [x] Cell-level AnnData with `obsm['spatial']` from centroids
- [x] `obs['x_centroid']`, `obs['y_centroid']`, `uns['mbsi_platform'] = 'xenium'`
- [x] Same analysis chain as Visium (QC → cluster → markers → SVG → domains)
- [x] Report export includes platform and ingestion metadata

### Generic h5ad / CSV

- [x] `.h5ad` with expression + `obsm['spatial']` (or x/y in obs)
- [x] CSV matrix + `coordinates.csv` with x/y columns
- [x] Routed through `ingest_dataset` with `generic_h5ad` profile

### API

- [x] `POST /api/dataset/upload` with `technology_hint=visium|xenium|generic_h5ad`
- [x] `POST /api/dataset/inspect` returns readiness + compatibility
- [x] `GET /api/dataset/readiness`
- [x] `POST /api/workflow/run` for `qc_transformation`, `visualization`, `spatial_variable_genes`, `spatial_domains`, `phenotyping`, `report_export`

## Smoke tests

```bash
PYTHONPATH=. python scripts/smoke_test_launch_imports.py
PYTHONPATH=. pytest tests/test_visium_ingestion.py tests/test_xenium_ingestion.py tests/test_real_data_workflow.py tests/test_io_visium.py tests/test_ingest_universal.py -q
```

## Out of scope (Milestone 1)

MERFISH, CosMx, Stereo-seq, CODEX, Spatial ATAC, Visium HD, foundation models, enterprise features, benchmark hub.

## Stubbed / deferred

- Full parsing of `cell_boundaries.parquet` geometry (path stored in `uns['xenium']['optional_artifacts']`)
- Full `transcripts.parquet` load into AnnData layers
- Morphology OME-TIFF raster load (path reference only)
- Visium HD binned outputs
- Legacy platform loaders (MERFISH, CosMx, CODEX, Stereo-seq, Spatial ATAC) return honest stubs via `ingest_dataset`
