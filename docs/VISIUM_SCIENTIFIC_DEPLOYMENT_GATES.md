# MBSI Studio — Visium scientific readiness and Lovable deployment gates

Source: user-supplied Biomni-style Visium platform audit, reviewed 2026-11-15.
This is an implementation tracker, **not a claim that the features below are complete**.

## Current implemented modules (reuse, do not duplicate)

- Ingestion: `mbsi/io/visium.py`, `mbsi/analysis/visium.py`, `mbsi/io/ingest_universal.py`.
- QC/normalization: `mbsi/workflows/xenium_pipeline.py`, `mbsi/analysis/seurat_like/`.
- Spatial statistics: `mbsi/analysis/spatial_stats.py` (effect sizes only; no FDR).
- Domains: `mbsi/domains/__init__.py` (expression graph, not validated spatial domain backend).
- Differential: `mbsi/statistics/replicate_aware.py`, `mbsi/statistics/pseudobulk.py`.
- CCI: `mbsi/communication/` (heuristic, hypothesis-level).
- TME: `mbsi/tme/pipeline.py`; gradients: `mbsi/gradients/`.
- Provenance and reports: `mbsi/schema/workflow_run.py`, `mbsi/discovery/spatial_workflow_evidence.py`, `mbsi/reports/final_report.py`.
- FastAPI: `mbsi/api/app.py`; Lovable-facing data routes are on backend PR #8.

## Hard scientific gates

1. **Biological condition DE:** no spot-level fallback. Require unique biological sample identity, at least two independent samples per condition, and a validated NB model. Until a PyDESeq2/edgeR adapter is implemented, return `blocked`; never publish MWU-on-sums as a validated DE result. Exploratory cluster markers are separate.
2. **Method fidelity:** do not label sklearn spectral clustering as Leiden, BayesSpace, STAGATE, or GraphST. Use actual backend or return `backend_unavailable` with no scientific artifact.
3. **SVG:** only declare significant SVG when an explicit spatial graph, test, and BH-adjusted p-value exist. Existing Moran/Geary effect sizes are descriptive only.
4. **CCI:** colocalization is not causation; annotate every CCI artifact `evidence_level=hypothesis`; missing cell-type reference/deconvolution must block cell-type-specific LR claims.
5. **Provenance:** capture actual runtime parameters, raw input hashes, versions, backend identity, random seeds, status, warnings, output hashes, and a stable evidence tier. Reports must be rendered from verified artifacts, not from generated narrative.
6. **Demo isolation:** synthetic or demonstration datasets must be visibly labeled and never mixed with observed patient/tissue results.

## Priority implementation phases and integration

| Phase | Backend adapter / action | API and Lovable surface | Required artifacts and acceptance |
|---|---|---|---|
| 0 Foundation | Repair `mbsi/analysis/visium.py` library IDs, image references, platform manifest; replace mislabeled clustering; keep raw sparse counts | Upload + Explore | Multi-sample ingest, coordinate/image alignment, real backend identity; public Visium fixture |
| 1 Spatial statistics | `squidpy.gr.spatial_neighbors` (Visium grid, appropriate coordinate type), `spatial_autocorr`, `nhood_enrichment`, `co_occurrence`, `interaction_matrix`, Ripley | `/api/workflow/run`, Explore SVG and neighborhoods | `svg.csv` with effect, `pval_norm`, `pval_norm_fdr_bh`; graph metadata; reference concordance |
| 2 Domains | Joint expression/spatial graph, explicit method selection; optional BayesSpace/STAGATE | Analyze + spatial map | `domains.csv`, per-spot labels, stability across graph settings |
| 3 Deconvolution | cell2location with scRNA reference; optional RCTD/Tangram | Upload reference + Analyze | `compositions.csv`, reference QC, uncertainty and reference sensitivity |
| 4 Replicate DE | Sparse raw-count sample×domain aggregation; PyDESeq2 or edgeR | Compare + blocked status | `pseudobulk_de.csv`, biological design, FDR, block tests |
| 5 CCI | Squidpy neighborhood enrichment; optional LIANA+ validated LR catalog | Analyze + CCI network | `cci.csv`, z-score, evidence level, proximity/label prerequisites |
| 6 Evidence | Persist manifests, versions/hashes, evidence tiers and facts gate | Reports + audit trail | `provenance.json`, artifact hashes, reproducible PDF, tamper tests |
| 7 HD | Visium HD 2/8/16um bins, chunked Zarr/Dask, image tiles, segmentation | HD upload + Explore | Memory budget, correct scale, public HD benchmark |
| 8 Validation | pytest lightweight + integration/heavy reference benchmarks | CI deployment gate | Cross-tool concordance, memory/runtime, no fabricated outputs |

## Lovable deployment contract

- Lovable owns `frontend/`; Python team owns `mbsi/`, tests, and API schemas.
- Set `VITE_MBSI_API_URL` to the **public HTTPS** FastAPI origin. `localhost` works only in local development.
- Set `MBSI_CORS_ORIGINS` to the exact Lovable production/preview origins. CORS is **not** authentication.
- Wire real `GET /api/v1/datasets`, `/features`, and `/spatial` from backend PR #8; remove disabled placeholder dataset query; invalidate queries after upload.
- Run and display actual workflow state; never infer completion from HTTP acceptance or fill missing results with demo values.
- Before exposing real patient data: implement authentication, authorization, tenant isolation, upload size limits, safe archive extraction, durable job queue, protected object storage, rate limits, and observability.
- Merge backend PR #8 **only after passing CI**, then rebase/merge Lovable PR #10 after verifying integration and hosted HTTPS health. A green frontend TypeScript build does not establish scientific readiness.

## Release levels

- **Development preview:** real observed-data ingest, Explore API, scientific unavailable/blocked states clearly visible.
- **Research beta:** validated Visium SVG/domain/DE/CCI core, provenance and facts gate, public reference benchmarks.
- **Production / patient data:** security/privacy review, durable compute, storage and recovery, validated deployment, and institution-approved compliance controls.

No claims of full Biomni-equivalent Visium analysis, clinical validity, or production deployment are authorized until these gates pass.
