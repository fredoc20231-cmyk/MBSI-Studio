# SpatialGE-Local archive assessment (17 November 2026)

Source reviewed: user-supplied `SpatialGE-Local-main.zip` (local archive; not a GitHub dependency).

## Decision: borrow workflow ideas, do not vendor or deploy this application

The archive contains a Streamlit application (`src/ge-app/app.py`), R analysis functions (`src/ge-app/R/analysis.R`), an `renv.lock` dependency lockfile, and example datasets. It requires Python, R, `spatialGE`, and a restored `renv` environment. Its README indicates that local uploads require a Google Cloud service account. No license file was found in the archive, so do not copy source code, UI assets, bundled datasets, or branding into MBSI Studio without appropriate rights and provenance.

Relevant *feature ideas* (not code imported):
1. Multi-sample pseudobulk PCA and heatmaps. MBSI should aggregate biological samples separately, display replicate/condition metadata, and reserve inferential DE for adequately replicated designs with validated negative-binomial methods.
2. Spatial quilt plots for the same gene across samples, aligned by sample identity and native coordinate system.
3. Spatial interpolation of gene expression, with interpolated maps clearly distinguished from observed expression and uncertainty displayed where supported.
4. Distribution plots and transparent filtering thresholds for spots/cells.
5. Spatial heterogeneity summaries as exploratory statistics, with a named, validated method and multiple-testing correction where applicable.

## Implementation boundary

The current deployment-recovery PR must remain a **FastAPI/React Render/Lovable** fix. Do not add Streamlit, R runtime, GCS service-account requirements, or bundled biological sample files to the API Docker image. Implement approved feature ideas as independently authored MBSI modules with tests and provenance in a separate scientific PR. This assessment does not establish method validity or production readiness.
