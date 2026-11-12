# Comparative Spatial Omics — real-data test guide (November 2026)

Status: **exploratory H5AD comparison ready for local verification**, NOT a fully validated universal spatial inference engine.

## Launch on the feature branch

```bash
git fetch origin
git switch feature/comparative-spatial-testing-20261112
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest tests/test_comparative_preview.py tests/test_api_entrypoint.py -q
SAFE=1 ./scripts/start_ui.sh
```

Open **http://localhost:8501** and select **Tissue Comparison** from the left navigation. If the standard launcher fails, run `streamlit run app/safe_streamlit_app.py`.

## Real data requirements

1. Provide two or more valid `.h5ad` files with samples already normalized to a *comparable* expression scale.
2. For sample annotations, each `adata.obs` must contain a categorical/string field like `cell_type`, `cluster` or `leiden`.
3. `adata.var_names` should contain **unique, comparable gene identifiers**. Genes must overlap across datasets.
4. For spatial tissue maps and gene overlays, `adata.obsm["spatial"]` must contain finite 2D coordinates (same within-sample units).
5. For accurate interpretation, annotate whether observations are cells, spots or bins, what normalization was used, and whether clusters were independently aligned.
6. This preview loads whole H5AD files into memory; for initial testing use appropriately sized specimens. Interactive map display is capped at 100,000 observations. For larger data implement Zarr-backed streaming.

## Functional controls

- Multi-file uploader, reference and comparison tissue selectors.
- Independent annotation selectors, overlapping gene selection, Run button.
- Side-by-side spatial cell/spot maps, gene-expression overlays.
- Descriptive matched-label composition table, proportion bar chart.
- Cross-tissue cluster-signature cosine similarity matrix; candidate correspondence only.
- Per-population gene-expression table, bar plot, difference heatmap.
- Within-section k-nearest-neighbor label fraction heatmaps.
- CSV exports and JSON method manifest.

## Important statistical limitations

- Matching uses **exact annotation names only**; it is not automated cluster correspondence and can be invalid if annotation labels differ in meaning.
- Relative population frequencies are *descriptive*, not differential abundance tests.
- Means and differences are on the current `.X` scale, without re-normalization, batch correction or cross-platform harmonization.
- Spatial-neighbor fractions are descriptive and are not statistical neighborhood enrichment.
- No inferential differential expression or TESSERA tests run in this preview.
- Different samples' coordinates are not registered.

## Next validated scientific integrations

| Package/project | Purpose | Status |
| --- | --- | --- |
| [TESSERA](https://github.com/floricaconstantine/TESSERA) (Artistic-2.0) | Multi-sample spatial Poisson regression; sample-specific spatial covariance and differential expression | Evaluated; pending R-worker adapter and independent validation |
| [SpatialData](https://github.com/scverse/spatialdata) | Canonical images, labels, points, shapes, tables and transforms | Planned full-store integration |
| [spatialdata-io](https://github.com/scverse/spatialdata-io) | Supported importers for major vendor data formats | Recommended, validate vendor/version outputs |
| [Squidpy](https://github.com/scverse/squidpy) | Spatial graphs, enrichment, spatial autocorrelation | Existing MBSI functionality; comparison validation needed |
| [BANKSY](https://github.com/prabhakarlab/Banksy_py) | Spatially aware domains / joint expression–neighborhood clustering | Benchmark candidate |
| [Vitessce](https://github.com/vitessce/vitessce) | Linked multiview, high-performance spatial genomics visualization | Recommended frontend upgrade |
| [TissUUmaps](https://github.com/TissUUmaps/TissUUmaps) | GPU-accelerated large-tissue spatial visualization | Performance reference |

Do not copy source code across repositories without respecting licenses. Prefer declared dependencies/adapters and version pinning.

## Scientific acceptance gate before broad release

Use multiple real vendor datasets; validate ingest provenance, normalize correctly, verify annotation equivalence, benchmark neighborhood statistics, validate sample-level inference, and ensure no fabricated or mock measurements appear in production UI.
