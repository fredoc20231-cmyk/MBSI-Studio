# MBSI Studio

Spatial omics web frontend for the existing [MBSI Studio repository](https://github.com/fredoc20231-cmyk/MBSI-Studio).

## Repository layout

This application's working root maps to `frontend/` in the source repository. The existing `mbsi/`, `app/`, API, scientific workflows and storage stay unchanged. Frontend changes enter `main` through separate pull requests; repository access through the GitHub API is not automatic two-way Git synchronization.

## Backend

All scientific computation runs in the existing FastAPI application, `mbsi.api.app:app`. The web frontend calls it through `src/lib/mbsi-api.ts`; no scientific analysis is reproduced here and no fabricated results are displayed.

Set `VITE_MBSI_API_URL` to the running API's base URL. A GitHub repository URL is source code, not a running API. Local development defaults to `http://localhost:8000`. No hosted API address has been supplied, so live analysis and uploads remain unverified.

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
