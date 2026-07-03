# AIStudio hand-off — wire the frontend to MBSI-Studio

Paste this to AIStudio. The backend is live and its JSON contract is frozen in
`mbsi_contract.ts`; a typed client is in `mbsiClient.ts`. Import both — do not
re-declare shapes.

## Setup
1. Copy `mbsi_contract.ts` and `mbsiClient.ts` into `src/api/`.
2. Add `VITE_API_BASE_URL` to `.env` (dev: `http://localhost:8000`; prod: deployed URL).
3. CORS is already open on the backend.

## Wiring (replace all mock data)
- **Technology dropdown (`StudySetupView`):** `listTechnologies()` → `technologies[]`.
  Render only after load; keep `currentTech?.resolution` as a guard. Every item now
  carries `resolution` and `type`, so the old TypeError is fixed at the source — not
  just masked by optional chaining.
- **Upload:** `uploadDataset(file, { projectId, technologyHint, sampleId })`. Handles
  the direct-POST fallback automatically when no cloud bucket is configured.
- **Run analysis:** `runWorkflow({ dataset_id, module?, params? })`.
  - Novice mode: send `{ dataset_id }` only (backend defaults).
  - Expert mode: send `module` + `params` (normalization, clustering resolution, and
    SVG `statistic`/`n_perms`/`fdr_alpha`). Populate expert control choices from the
    selected technology's `normalization` / `clustering` / `compatible_analyses`.
- **Poll:** `pollJob(runId, onTick)` → resolves on `completed` | `failed` | `not_found`.
- **Render (`TissueCanvas`):** `getSpatialData(projectId, { datasetId, genes, maxCells })`.
  Use `cells[].x/y` for coords, `cluster` for color-by-cluster, `expression[gene]` /
  `normalizedExpression[gene]` for color-by-gene (gene from `genesList`). Show a
  "showing N of M" note when `warnings` mentions subsampling.
- **QC panel:** `qcScore`, `mitochondrialRatio`, `detectedCellsCount`,
  `detectedGenesCount`; render `validations[]` as passed/warning/failed pills.

## Endpoints (all verified against real TNBC data, zero contract drift)
| Endpoint | Returns |
|----------|---------|
| `GET /api/technologies/frontend` | `{ technologies: Technology[] }` (12 platforms) |
| `GET /api/projects/{id}/spatial-data` | `SpatialDataPayload` |
| `POST /api/upload/sign` | `UploadSignResponse` |
| `POST /api/dataset/upload` | dataset record (multipart) |
| `POST /api/workflow/run` | `WorkflowRunResponse` |
| `GET /api/jobs/{id}/status` | `JobStatus` |

## The one thing AIStudio cannot do itself
It has no running backend, so it can only mock. Point it at a running MBSI-Studio
(localhost during dev, or a deployed URL) to test live. Because the mock shapes in
`mbsi_contract.ts` equal the real shapes, nothing changes when you switch to live.

## Definition of done for AIStudio
`npm run build` + lint pass; no `any` on API responses; all views read live data via
`mbsiClient`; report the diff of changed files.
