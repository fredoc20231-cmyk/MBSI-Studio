# iVisio legacy code review — selective adoption (2026-11-18)

Source: user-provided `iVISIO-claude-new-app-jeexkm.zip`. The archive includes a FastAPI/Scanpy/Squidpy backend, Vite/React/Plotly frontend, tests, Docker files, and an earlier R Shiny `legacy/app.R`. This is **user-owned legacy reference material**, not an external runtime dependency.

## Decision

**Adopt useful patterns and independently port validated functionality into existing MBSI modules; do not overwrite or vendor the whole app.** MBSI already has a broader multi-platform data model, provenance requirements, Lovable UI, and deployment integration. A second application stack and session model would introduce conflicts.

| Priority | Legacy source | Useful capability | Integration requirements |
|---|---|---|---|
| P1 | `frontend/src/components/SpatialTab.tsx`, `ExploreTab.tsx`, `MatrixTab.tsx` | Interactive tissue overlays, feature exploration, dot plots, heatmaps and violins | Adapt into existing MBSI frontend; use observed dataset API, real gene IDs, scale factors, legend and export |
| P1 | `backend/app/pipeline.py`, `QCTab.tsx`, `NormalizeTab.tsx` | QC distributions, filtering, PCA diagnostics, Scanpy/Leiden/UMAP pipeline | Preserve raw counts and sample metadata, document normalization, validate sparse and small-data cases |
| P1 | `backend/app/advanced.py`, `SpatialStatsTab.tsx`, `SVGTab.tsx` | Moran's I, neighborhood enrichment, co-occurrence, spatial statistics | Check coordinate systems and neighborhood definitions; add p-values/FDR, seed, method and evidence provenance |
| P2 | `frontend/src/components/IntegrationTab.tsx` | Multi-slide integration and batch-effect diagnostics | Keep biological sample identity, compare uncorrected and corrected results; no false biological inference from integration |
| P2 | `backend/app/stie.py`, `STIETab.tsx`, `backend/tests/test_stie.py` | Experimental spot-expression + nuclear morphology reconstruction, gap-cell assignment and EM diagnostics | **Do not label validated STIE or cell-level truth yet**. Audit equations against publication/reference implementation, nuclear coordinate registration, signature alignment, uncertainty, segmentation dependence, benchmarks and biological controls. The module explicitly uses an NNLS surrogate rather than identical reference optimization. |
| P2 | `MarkersTab.tsx`, `LigRecTab.tsx`, `AITab.tsx` | Exploratory markers, ligand-receptor visualization, local annotation, enrichment | Cluster markers are not condition-level DE. Require biological-replicate-aware condition DE; ligand-receptor scores are hypotheses, not proven communication; annotation needs calibrated evidence |
| P3 | `TrajectoryTab.tsx`, `ExportTab.tsx` | PAGA, diffusion pseudotime, export layout | Trajectory inference only when scientifically appropriate; reports must cite exact dataset/run/parameters and distinguish inferred from observed data |

## Technical and scientific red flags

- `backend/app/main.py` sets `allow_origins=["*"]`, unsuitable for authenticated production/clinical deployments.
- `backend/app/state.py` provides a session store, not MBSI's desired durable, tenant-isolated project/run storage.
- `backend/app/main.py` writes uploaded files to temporary paths and reads entire uploads into memory; requires upload limits, validation, lifecycle cleanup, and authorization before reuse.
- `backend/app/pipeline.py` uses Scanpy `rank_genes_groups` for marker discovery. **Do not reuse it as replicate-aware condition differential expression.**
- `backend/app/pipeline.py` describes Pearson residuals as an SCT *analog*, not equivalent to Seurat SCTransform.
- The STIE module's own docstring describes an approximate NNLS surrogate of the published method; claims of faithful reproduction and cell-level accuracy require independent validation.
- The bundled synthetic demo data and its tests demonstrate behavior on synthetic inputs, **not** accuracy on Visium, Visium HD, Xenium or clinical samples.
- Legacy frontend components cannot simply replace the existing Lovable workspace and MBSI API contracts.

## Adoption gates

1. Preserve current deployment repair PR scope; do not add the legacy backend, Docker images, dependencies, or session store to the Render service.
2. Open a separate scientific feature PR, starting with interactive expression matrix/QC plots and sample-level integration diagnostics.
3. Port each module with explicit input/output schemas, raw-vs-transformed expression labels, sample-aware metadata, reproducibility, failure modes, and tests on real and synthetic fixtures.
4. Benchmark STIE-like reconstruction against published reference outputs and segmented imaging-based ground truth; report calibration, uncertainty, sensitivity, and failure cases before exposing as validated.
5. Keep all AI labels, pathway enrichment and ligand-receptor inference evidence-linked; abstain when missing prerequisites.

No code from this archive has been merged as an analysis implementation in this assessment commit.
