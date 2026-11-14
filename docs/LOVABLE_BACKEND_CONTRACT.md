# Lovable frontend ↔ MBSI Studio scientific backend

## Responsibilities

- **Lovable (frontend):** React/TypeScript application, white and purple Loop-like
  navigation, user flows, responsive viewer, metadata and sample filters,
  microscope image channels, interactive linking, analysis job status.
- **MBSI (backend):** FastAPI, observed-data ingestion, spatial transcriptomics
  analysis, segmentation, Visium/HD/Xenium coordinates and spatialGE R backend,
  analysis provenance, permissioned storage, scientific report exports.
- **Single API source of truth:** `mbsi.api.app:app` via `create_app()`.
  Do not create a second production analysis backend in Lovable.
- **Local development:** frontend `http://localhost:3000`, backend
  `http://localhost:8000`. FastAPI generates `/openapi.json` and
  `/docs` for client generation.
- **CORS:** set `MBSI_CORS_ORIGINS` to the explicit Lovable preview/deployment
  domain(s); do not set `*` for hosted patient-derived data.
- **Auth/security:** This contract is **development only** until identity,
  organization authorization, dataset ownership, upload size quotas, HTTPS,
  durable object storage, audit logging and access controls are completed.
  CORS is not authentication. Do not expose private biomedical datasets.

## Current API routes

- `GET /api/health` / `GET /api/technologies`
- `POST /api/project/create`, `POST /api/project/update`
- `POST /api/dataset/upload` (multipart file + query parameters),
  `POST /api/dataset/inspect`, `GET /api/dataset/readiness`
- `POST /api/workflow/run`, `GET /api/workflow/status`,
  `GET /api/results/list`, `GET /api/findings/list`,
  `GET /api/evidence/list`, `POST /api/report/generate`
- `POST /api/v1/imaging/layout`: return validated, user-provided
  multiplex FoV/image embedding points with metadata
- `POST /api/v1/imaging/embedding`: compute deterministic PCA/t-SNE
  visualization coordinates from **supplied observed image feature vectors**.
  This is inspired by Mistic's image t-SNE workflow but is independently
  implemented. The API does not yet ingest raw multiplex TIFF/QPTIFF or
  generate image thumbnails.

## Imaging request example

```json
{
  "image_ids": ["field_01", "field_02", "field_03"],
  "features": [[1.5, 0.3, 3.1], [1.1, 0.8, 4.2], [0.4, 2.2, 1.4]],
  "metadata": {
    "field_01": {"platform": "CODEX", "sample_id": "sample_A"},
    "field_02": {"platform": "CODEX", "sample_id": "sample_A"},
    "field_03": {"platform": "CODEX", "sample_id": "sample_B"}
  },
  "method": "pca"
}
```

Returns: `status`, `source`, `coordinates` array of
`{image_id, x, y, platform?, sample_id?, ...}`.

## Local developer instructions

```bash
python -m pip install -e '.[dev]'
uvicorn mbsi.api.app:app --reload --host 127.0.0.1 --port 8000
# in another terminal
streamlit run app/streamlit_app.py
```

Frontend client generation: use `http://localhost:8000/openapi.json`,
e.g. `openapi-typescript`, to create typed TypeScript request/response types.
Use an API client with a configurable `VITE_MBSI_API_URL`. For real-time run
status poll `/api/workflow/status?run_id=...` only after `/api/workflow/run`
returns, then stop polling on terminal state. WebSocket/SSE is **not yet**
implemented, and current workflow execution is synchronous.

## Mistic scope and attribution

Upstream: [MathOnco/Mistic](https://github.com/MathOnco/Mistic), MIT,
Copyright (c) 2021 IMO. Study its license and [Patterns paper](https://www.cell.com/patterns/fulltext/S2666-3899(22)00120-9).

Mistic contributes the imaging exploration concept: multiplex marker channel
selection (Vectra, CODEX, CyCIF, t-CyCIF), paired t-SNE scatter and montage
canvases, metadata coloring, optional user-provided embeddings, hover and
image exploration. The first MBSI module implements only **embedding
calculation and metadata-aligned coordinates**. The user interface for
image montage/linked selections, TIFF ingestion and feature extraction
remain separate tasks. In no case infer clinical response from an image
embedding without validated studies.

## Lovable build brief

Build the MBSI Studio frontend in `frontend/` using React, TypeScript and
a generated OpenAPI client. Maintain familiar clean-white tissue-analysis
navigation with purple highlights: Explore, Analyze, Compare, Integrate,
Annotation, Reports. Separate left-side study/sample tree, central tissue map,
right-side feature inspector and lower analysis-tool dock. In Explore,
provide linked sample maps and genes; in Imaging, add marker-selection,
image-cohort t-SNE/PCA map, thumbnails and per-FoV metadata **only after**
backend endpoints are supported. Never hardcode fake patient results; empty
states should prompt upload and label unavailable features. Provide
accessible keyboard navigation, responsive layout and clear provenance.

**Release rule:** Lovable frontend may deploy independently to a preview
environment but should never advertise results as computed until the API
returns real observed outputs. Backend and frontend changes enter main
through separate PRs with contract and integration tests.
