# MBSI Studio

Spatial omics web frontend for the existing [MBSI Studio repository](https://github.com/fredoc20231-cmyk/MBSI-Studio).

## Repository layout

This application's working root maps to `frontend/` in the source repository. The existing `mbsi/`, `app/`, API, scientific workflows and storage stay unchanged. Frontend changes enter `main` through separate pull requests; repository access through the GitHub API is not automatic two-way Git synchronization.

## Backend

All scientific computation runs in the existing FastAPI application, `mbsi.api.app:app`. The web frontend calls it through `src/lib/mbsi-api.ts`; no scientific analysis is reproduced here and no fabricated results are displayed.

Set `VITE_MBSI_API_URL` to the running API's base URL. A GitHub repository URL is source code, not a running API. Only local development hosts default to `http://localhost:8000`; hosted previews without configuration make no request to the visitor's localhost. No hosted API address has been supplied, so live analysis and uploads remain unverified.

The **Scientific backend** control checks `/api/health` against the repository's health contract before selecting an address. The override lasts for the current browser tab, contains no credentials and is not a substitute for deployment configuration. All upload, workflow and result requests then use that same service through `src/lib/mbsi-api.ts`. Changing services clears session query data so dataset identifiers do not cross services. Upload errors preserve the backend's returned rejection reason. A file picker accepting all files does not imply the scientific backend supports FASTQ, arbitrary slides or multi-file bundle ingestion.

### Run the repository's API without changing its scientific code

From the source repository root, use its existing `Dockerfile`:

```sh
docker build -t mbsi-api .
docker run --rm -p 8000:8000 \
  --mount type=bind,source="$(pwd)/data",target=/app/data \
  -e MBSI_CORS_ORIGINS="http://localhost:8080,http://127.0.0.1:8080,https://spatial-omics-studio.lovable.app,https://mbsi-studio.cronus.life,https://id-preview--5fcd3a35-f644-4f85-9c3a-6112d651ea0e.lovable.app,https://5fcd3a35-f644-4f85-9c3a-6112d651ea0e.lovableproject.com" \
  mbsi-api uvicorn mbsi.api.app:app --host 0.0.0.0 --port 8000
```

Create `data/` before running and retain it as durable storage. For hosted use, run this existing container on a host with HTTPS and access controls, then set `VITE_MBSI_API_URL` to that host (without `/api/health` or `/docs`) and publish the frontend. The `Scientific backend` connection checker also accepts a copied health/docs URL and removes its suffix. On local HTTP development, the repository API on `http://localhost:8000` is supported. The hosted HTTPS app rejects HTTP service addresses. This does not deploy a Python service inside the frontend's serverless runtime.

On the API host, set `MBSI_CORS_ORIGINS` to an explicit comma-separated list of permitted frontend origins, including the local development origin and the actual preview/deployed origins. Never use a wildcard for patient-derived data. CORS is not authentication: do not expose private biomedical data until identity, organization authorization, dataset ownership, upload quotas, HTTPS, durable storage, audit logging and access controls are in place.

The inspected source revision supports the `/api/*` project, dataset, workflow, results, findings, evidence and report contract. It does not yet expose `/api/v1/imaging/embedding`; imaging computation therefore remains unavailable until implemented in the existing backend. This frontend does not add a substitute endpoint.

## Development

From the source repository's `frontend/` directory:

```sh
bun install --frozen-lockfile
bun run dev
bun run test
```

Copy `.env.example` to `.env.local` for local frontend configuration. Never commit credentials, private datasets, dependency directories or build output. The TanStack package versions are pinned to the target application's versions.
