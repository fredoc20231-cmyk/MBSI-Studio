# MBSI Studio User Guide

## Platform overview

MBSI Studio is a physics-aware spatial biology intelligence platform for end-to-end spatial omics workflows. The SaaS shell organizes analysis into guided modules: project setup, QC, visualization, spatial statistics, MBSI reconstruction, discovery intelligence, and report export.

Use the header to monitor project context, technology, dataset status, and run status. Help, Settings, and Notifications are available from the top bar.

## Supported technologies

MBSI Studio supports technology-aware ingestion and module compatibility for major spatial platforms, including:

- **Visium / Visium HD** — spot-based spatial transcriptomics
- **Xenium** — subcellular spatial transcriptomics
- **CosMx SMI** — high-plex spatial molecular imaging
- **MERFISH / seqFISH** — single-molecule FISH platforms
- **Stereo-seq** — nanoscale spatial omics
- **CODEX / multiplex IF** — protein spatial imaging

Select your technology in **Study Setup & Data** before upload. Required and optional file types are shown per platform.

## Workflow guide

1. **Study Setup & Data** — define project metadata, experimental design, sample table, and upload spatial files.
2. **QC & Transformation** — filter, normalize, and prepare AnnData for downstream analysis.
3. **Core Spatial Analysis** — visualization, SVG, gene sets, domains, phenotyping, differential analysis, gradients.
4. **MBSI Intelligence** — segmentation, physics-aware reconstruction, benchmark, discovery, AI review.
5. **Report & Export** — notebook, HTML/PDF report, and data bundle downloads.

The left navigation groups modules by workflow stage. Use **Run next step** in the sidebar for guided progression.

## Dataset requirements

Minimum requirements for most modules:

- AnnData (`.h5ad`) or platform-native count matrices with spatial coordinates
- Sample metadata CSV (recommended)
- Technology-specific assets (e.g., histology image, segmentation mask) when required by the selected platform

Dataset status in the header reflects session state:

| Status | Meaning |
|--------|---------|
| UNVERIFIED | No AnnData loaded, or data present but validation incomplete |
| VALIDATING | Upload or workflow validation in progress |
| READY | Dataset validated (readiness score ≥ 70 or validators passed) |
| CORRUPTED | Validation or ingestion failed |

Sample datasets can be loaded explicitly from **Study Setup & Data** for exploration; they are labeled on that page only.

## Documentation links

- API health: `http://127.0.0.1:8000/health`
- Repository docs: `docs/` directory
- Schema reference: `mbsi/schema/`
- Smoke test: `python scripts/smoke_test_launch_imports.py`

## Contact / support

MBSI Studio runs in **local mode** by default (no authentication). For support:

- Review validation warnings in the notification center
- Check backend status in the footer status bar
- Open **Settings → About** for version and build metadata

For production deployments, configure the API endpoint and storage location under **Settings → Platform**.
