# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multi-omics data loaders: MERFISH/MERSCOPE, CosMx, CODEX, spatial ATAC
  (5 platforms now functional alongside Visium, Xenium, generic h5ad).
- Spatially-variable-gene (SVG) detection engine (`mbsi/analysis/svg.py`) with
  permutation-based Moran's I and BH-FDR; CLI (`scripts/run_svg_detection.py`).
- AIStudio frontend integration: `mbsi/api/aistudio.py`, TypeScript contract and
  client under `docs/frontend_contract/`.
- Production deployment scaffolding: GitHub Actions CI (lint + test matrix +
  image build + dependency scan), `docker-compose.prod.yml`, `.env.example`,
  pinned `requirements.lock.txt`, `LICENSE`, `SECURITY.md`.
- API readiness/liveness probes: `/readyz`, `/healthz` (alongside existing `/health`).
- Configurable CORS origins via `MBSI_CORS_ALLOW_ORIGINS`.

### Changed
- Technology catalog entries now expose `functional` / `loader_status` fields.
- `discovery` compatibility status resolves to `unavailable` (with an upload
  recommendation) when no dataset is loaded.

### Fixed
- Per-sample ingestion no longer requires a live Streamlit runtime
  (histology auto-extract guarded behind a lazy import).
- Full test suite green (319 passed).

## [0.2.0]
- Physics-aware spatial reconstruction, benchmark hub, discovery engine,
  TME intelligence, Streamlit UI, FastAPI service.
