# MBSI Studio — Lovable / React Master Build Brief

**Objective:** Build an institutional-quality, browser-native, evidence-based Spatial Omics Studio using the scientific backend in this repository. Make the interface powerful, polished, accessible, fast and fully functional. Do not confuse a visual prototype with a validated scientific analysis.

**Source of truth:** This repository's FastAPI server on port 8000, OpenAPI at `/openapi.json`, and API status at `GET /api/v2/capabilities`. Do not replace the existing scientific backend with fake JavaScript calculations. Keep the Python/Scanpy/SpatialData roadmap independent of the frontend project.

## Lovable handoff
1. Start a **new Lovable frontend project**, using this brief as the design and functional contract. Do not assume Lovable can directly import this existing Python monorepo or run a Streamlit server.
2. Use React + TypeScript + Tailwind + shadcn/ui (or the project's supported equivalents). Connect to the existing FastAPI via `VITE_MBSI_API_BASE_URL`. In local dev `http://localhost:8000`; deployment must use an authenticated HTTPS API. No secrets in browser code.
3. Reference `frontend/lovable/mbsi-api.ts` for typed HTTP calls; use runtime schema validation when integrating.
4. The first release is a **real-data explorer and descriptive tissue comparison**. For unsupported scientific analyses, show an honest "Not available yet" panel and method requirements; never fake results or unconnected controls.
5. Do not upload protected clinical or identifiable data to Lovable preview systems. Use synthetic fixtures in UI development only, prominently watermarked "SYNTHETIC DEMO".

## Product identity
- Name: **MBSI Studio — Spatial Omics Intelligence**
- Purpose: advanced 10x Visium / Visium HD roadmap, Xenium, multiplaform spatial transcriptomics and cross-tissue biological comparison.
- Scientific direction: physics-aware, reproducible, multimodal spatial biology.
- Appearance: premium analytical software rather than a marketing landing page. Dark graphite/navy and ivory themes, consistent compact typography, subtle surfaces, saturated data colors reserved for charts and tissue overlays.
- Screen organization: narrow primary left navigation (collapsible), top project/sample context, central analysis canvases, collapsible right inspector, bottom job/status strip. Responsive 2-panel desktop, usable tablet/mobile read-only view.

## Required working navigation
1. **Overview**: data readiness, real sample count, analysis state, provenance and supported assay types.
2. **Study & Samples**: create project; upload H5AD or supported Space Ranger ZIP with progress; inspect validation/warnings; list dataset IDs; edit condition/subject metadata only where backend implements persistence.
3. **10x Visium Analysis**: sample QC and tissue maps; gene explorer with gene search; display assay resolution and spatial coordinate caveats. Native HD 2/8/16 µm bin selection **not yet implemented**. Present clearly labeled roadmap.
4. **Spatial Atlas**: linked gene and annotation tissue plots, legend, pan/zoom, real coordinate systems; display raw counts versus normalized values correctly.
5. **Region of Interest (ROI)**: enable a draggable rectangle on the tissue scatter map in source-data coordinates. Call `POST /api/v2/datasets/{id}/roi/summary` and display actual region cell/spot counts, annotation fractions, and selected gene means; show empty-region warnings. ROI is descriptive and not a registered cross-sample shape.
6. **Cluster & Cell Types**: annotations, proportions, cluster-similarity matrix; unknown/unmatched labels clearly displayed.
7. **Compare Tissues**: select 2 uploaded samples, their compatible annotation fields and a shared gene panel, submit `/api/v2/comparisons/preview`, render composition charts, differential mean heatmaps, similarity and limitations.
8. **Spatial Neighborhoods**: connect only to validated backend outputs; the current Streamlit exploratory neighbor matrix must not be silently substituted for inferential enrichment.
9. **Pathways / Communication**: capability-aware; buttons disabled and explain requirements unless an actual supported backend route is confirmed by OpenAPI.
10. **AI Interpretation**: only evidence-bound result summaries; no invented biomarkers, mechanisms, p-values or clinically actionable claims.
11. **Reports**: display provenance, real downloadable outputs via existing supported API; build export from frontend preview only when supported and explicitly label as descriptive.
12. **Settings**: backend URL (read-only indication), auth status, theme, data policy, method/version labels.

## Screens and interactions
- Each navigation item must lead to a real route; every visible control must have an effect, validation message, or clearly disabled state.
- Dataset cards: platform, sample ID, number of units, number of genes, spatial availability, annotation keys, readiness and limitations.
- Gene search: debounced query against `GET /api/v2/datasets/{id}/genes?query=...&limit=...`.
- Tissue plot: `GET /api/v2/datasets/{id}/spatial-points?annotation=...&gene=...&limit=...`; render as performant WebGL scatter, with reversed y axis only when appropriate to reported coordinate conventions. Do not imply registration of different tissues.
- Comparison request: `POST /api/v2/comparisons/preview` with the exact fields in OpenAPI. Handle 422 errors and empty intersections gracefully.
- Client state: dataset selections, filters, annotation keys, shared genes, active chart layer, data provenance, server pending/error states.
- Include a compact feature status legend: Supported / Preview / Experimental / Planned. Do not make badges imply analysis validity.
- Accessibility: keyboard navigation, labels, color-blind-safe cluster palette, downloadable tabular alternatives, error recovery.

## 10x Visium-specific visualization target
Visium v1/v2: tissue image overlay, spots, markers, spatial domains, cluster vs gene view, matched samples, ROI, results notebook.
Visium HD: future canonical support for Space Ranger `binned_outputs/square_002um`, `square_008um`, `square_016um`, segmented output matrices and image pyramids. The backend must resolve the chosen observation unit and coordinate transformations before a frontend represents this feature as operational.
Image viewer roadmap: SpatialData + OME-NGFF / Zarr and Vitessce or deck.gl for GPU-based tile rendering. Current `spatial-points` API is bounded scatter data, not an image tile server.
Expected higher-level analytics compared to basic aggregation: cross-sample cluster correspondence, matched-population expression changes, neighborhood contrasts, region/ROI comparison, replicate-aware inference, gene program differences, evidence-backed findings.

## Backend endpoints to wire now
- `GET /api/health`, `GET /api/v2/capabilities`
- `GET /api/technologies`, `POST /api/project/create`
- `POST /api/dataset/upload` (multipart `file`; query `project_id`, `sample_id`, `technology_hint`)
- `POST /api/dataset/inspect` and `GET /api/dataset/readiness?dataset_id=...`
- `GET /api/v2/datasets/{dataset_id}/summary`
- `GET /api/v2/datasets/{dataset_id}/qc`
- `GET /api/v2/datasets/{dataset_id}/genes`
- `GET /api/v2/datasets/{dataset_id}/spatial-points`
- `POST /api/v2/datasets/{dataset_id}/roi/summary`
- `POST /api/v2/comparisons/preview`
- `POST /api/workflow/run`, `GET /api/workflow/status?run_id=...`
- `POST /api/report/generate` only where supported by actual backend response

**Important:** No project-wide dataset listing or authenticated collaboration yet. Use upload return IDs and an explicit local session registry for the frontend preview. Do not invent a list endpoint. No native browser CORS wildcard: set `MBSI_CORS_ORIGINS` on the backend to the exact frontend origin.

## Engineering deliverables
- Usable React application with real API integration and deterministic error handling.
- Schema-driven request and response types, typed query hooks, responsive dashboards.
- Tissue overlays with color legends, gene-expression slider and sample inspector.
- Comparative matrix / composition bars / expression heatmap / export only real backend outputs.
- Component tests and browser end-to-end tests for uploading, selecting, visualizing, comparing and error handling.
- A `README.md` describing environment variables and how to run with local FastAPI.
- Run-through acceptance: 2 test H5AD files upload; annotations appear; 2 spatial maps render; gene search works; comparison runs; no fabricated p-values; browser refresh restores non-sensitive selection state only.

## Explicit DO NOT
- Never replace missing data with realistic fake numbers in production.
- Never run complex analysis in the browser.
- Never claim two clusters match because their numeric IDs are equal.
- Never call cell-level observations independent patient replicates.
- Never claim complete Visium HD support on this backend until ingest, scale mapping and full round-trip tests pass.
- Never place PHI, API secrets or raw patient content in localStorage, analytics or logs.
- Never show an enabled button that has no verified action.
- Never market preview outputs as diagnostic, clinical or regulated use.

## Scientific/backend upgrade milestones
P1: real Visium HD validated loader and SpatialData-backed image/geometry store.
P2: full tissue tile serving and joint multiview views.
P3: replicate-aware pseudobulk and matched study designs.
P4: spatial differential inference with an independently tested TESSERA R worker.
P5: pathway, cell communication, spatial interaction null models.
P6: benchmarking, permissions, audit controls, cloud deployment and reproducible reports.

Only mark a milestone completed once it passes actual data fixtures and test-suite acceptance.
