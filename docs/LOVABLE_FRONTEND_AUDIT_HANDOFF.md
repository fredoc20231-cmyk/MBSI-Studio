# Lovable handoff — observed-data MBSI Studio UI

**Repository:** https://github.com/fredoc20231-cmyk/MBSI-Studio
**Source branch:** latest `main` (frontend and backend PR #8 are merged).
**Production frontend:** https://mbsi-studio.cronus.life
**Backend:** configure `VITE_MBSI_API_URL` to the actual Render HTTPS origin (not localhost).
**Scientific W1–W8 additions:** PR #13 is under validation; do not enable its controls until merged and deployed.

## Implement the five-stage user journey

1. **Study setup.** Call `GET /api/technologies`, `POST /api/project/create`; upload Space Ranger ZIP or supported files with `POST /api/dataset/upload?project_id=...&technology_hint=visium&sample_id=...` using multipart field `file`. Show actual readiness, warnings, sample/library metadata. Folder uploads are not automatically supported by a single-file multipart API: package ZIP client-side only if supported/validated, otherwise require ZIP.
2. **QC.** `POST /api/workflow/run` with `{project_id,dataset_id,module:"qc",params:{},allow_demo:false}`. Display exact outputs and warnings; no synthetic QC metrics.
3. **Explore / analysis.** Use `GET /api/v1/datasets` (response `{datasets:[]}`), `GET /api/v1/datasets/{id}/features?query=...`, and `GET /api/v1/datasets/{id}/spatial?gene=...` or `?annotation=...`. Show coordinate source, layer, total/returned observations and downsampling. Advanced SVG/niche/DE/CCI controls are feature-gated pending PR #13 routing and scientific acceptance.
4. **Results & evidence.** `GET /api/results/list?dataset_id=...`, `/api/findings/list`, `/api/evidence/list`. Show evidence tier and exact warning strings. No causal claims from colocalization or ligand–receptor hypotheses.
5. **Report.** `POST /api/report/generate` with `{project_id,dataset_id,run_id,report_type:"html"}`. Render actual `output_files` only if accessible and authorized.

## Run lifecycle and blocked states

Current `/api/workflow/run` may execute synchronously. Do **not** assume a queue exists. If the response contains a running/queued state, poll `GET /api/workflow/status?run_id=...`; otherwise show its terminal state immediately. Persist active run IDs so navigation does not lose state. Show `blocked`, `backend_unavailable`, `failed`, `not_ready` explicitly; never convert blocked analyses into empty success tables. Every API `warnings[]` must remain visible.

## API contract and security

- `/api/health` returns `{status,version,...}`.
- `VITE_MBSI_API_URL` is the existing client variable. Do not silently change it to `VITE_API_BASE_URL`.
- Set Render `MBSI_CORS_ORIGINS=https://mbsi-studio.cronus.life` (add explicit preview origins separately).
- Verify payloads against **deployed** `/openapi.json`; the scientific branch may not yet be deployed.
- No real patient uploads until authentication, tenant isolation, durable protected storage, upload limits, and security review are complete. CORS is not authentication.
- Large uploads: real progress, HTTP 413 and timeout handling; do not promise resumable/multi-GB uploads without a supported resumable transport.
- Avoid placeholder values, false claims of successful workflow execution, invented images, or artificial spatial expression.

## Lovable deliverables

- Keep current workspace and responsive design, add a persistent five-stage navigation and dataset status.
- Wire the disabled dataset queries in Workspace and Compare to the real dataset list endpoint; invalidate on successful upload.
- Provide accessible gene search, spatial scatter/tissue overlay (only if actual tissue image exists), tables, legends, loading/empty/error states, and provenance panels.
- Add TypeScript, lint and browser integration tests against the actual deployed API.
- Commit changes in a **new frontend PR targeting main**; merge only after CI and deployed smoke tests pass.

## Scientific release warnings

Condition-level DE requires at least two independent biological replicates per condition **and** a validated NB model; spot count does not equal replicate count. SVG significance requires explicit graph/test/FDR metadata. Cell-cell interaction results remain hypothesis-level. Visium HD remains a later, gated phase.
