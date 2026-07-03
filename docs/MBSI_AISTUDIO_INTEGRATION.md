# MBSI-Studio ↔ AIStudio Frontend Integration

Backend changes that make MBSI-Studio's FastAPI serve exactly the JSON contract
the AIStudio React frontend consumes. **Claude/MBSI = backend brain; AIStudio = UI.**

## 1. Root-cause fix for the `StudySetupView` TypeError

The crash (`Cannot read properties of undefined (reading 'resolution')`) had two layers:

1. **Timing** — `technologies[]` empty during load. AIStudio's optional-chaining
   patch (`currentTech?.resolution`) correctly guards this.
2. **Contract mismatch (the real bug)** — even once loaded, the backend's
   `/api/technologies` emitted `resolution_class` + `supports_*` flags but **no
   `resolution` and no `type` field**. So `currentTech.resolution` was `undefined`
   by design, and every tech showed "N/A".

**Fix:** every technology entry now carries `id`, `name`, `resolution`, `type`
(additive — the old `resolution_class`/`display_name`/`supports_*` keys are
untouched, so nothing else breaks). Use `GET /api/technologies/frontend` for the
guaranteed-shape list, or the enriched `GET /api/technologies`.

## 2. Technology catalog — 12 platforms

| key | name | resolution | type | milestone |
|-----|------|-----------|------|-----------|
| visium | 10x Visium | 55 µm spots | Sequencing-based | functional |
| visium_hd | 10x Visium HD | 2–8 µm bins | Sequencing-based | coming_later |
| xenium | 10x Xenium | Subcellular (~0.2 µm) | Imaging-based | functional |
| merfish | MERFISH / MERSCOPE | Subcellular | Imaging-based | coming_later |
| cosmx | NanoString CosMx | Single-cell / subcellular | Imaging-based | coming_later |
| stereo_seq | STOmics Stereo-seq | 220–500 nm (DNB) | Sequencing-based | coming_later |
| codex | CODEX / multiplex IF | Single-cell (protein) | Imaging-based | coming_later |
| spatial_atac | Spatial ATAC | Spot / bin (epigenome) | Sequencing-based | coming_later |
| slide_seq | Slide-seq / V2 | 10 µm beads | Sequencing-based | coming_later |
| seqfish | SeqFISH+ | Subcellular | Imaging-based | coming_later |
| exst | Expansion ST (ExST) | Subcellular (expansion) | Imaging-based | coming_later |
| generic_h5ad | Generic AnnData / CSV | Variable | Generic | functional |

`seqfish` and `exst` were added to complete the user's requested platform list.
"functional" = full Milestone-1 ingest+analysis today; "coming_later" = catalog +
loader present (some stubbed), enrichable per-platform.

## 3. Endpoints (new)

### `GET /api/technologies/frontend`
`{ "technologies": [ {id, key, name, resolution, type, modality, milestone_functional,
required_files, supports_images, supports_segmentation, ...}, ... ] }`

### `GET /api/projects/{project_id}/spatial-data`
Query: `dataset_id`, `genes` (comma-sep), `max_cells` (default 5000), `max_genes` (default 12).
Returns the AIStudio spatial contract — **all values computed from the real AnnData**:
```
{ technology, matrixDimensions, detectedCellsCount, detectedGenesCount,
  mitochondrialRatio, qcScore, histologyImageUrl, genesList,
  cells: [{id, x, y, cluster, total_counts, n_genes_by_counts, pct_counts_mt,
           expression{}, normalizedExpression{}}],
  validations: [{name, status, message}], warnings: [] }
```
- QC (`total_counts`, `n_genes_by_counts`, `pct_counts_mt`) read from `obs`, else recomputed.
- `pct_counts_mt` from `MT-` prefix genes; `qcScore` a transparent monotone function of
  median genes / mito% / depth.
- Coordinates from `obsm['spatial']` (fallback `obs[x,y]`).
- Cells deterministically subsampled (seed=0) above `max_cells`; genes = requested ∩ present,
  else top-variance.

### `POST /api/upload/sign`
Body `{filename, contentType}` → presigned-upload descriptor. With no cloud bucket
configured returns a **direct-upload fallback** (`mode:"direct"`, `uploadUrl:"/api/dataset/upload"`),
so the frontend upload flow works locally. Swap in a GCS/S3 signer for cloud deploys.

### `GET /api/jobs/{job_id}/status`
`{jobId, status, module, outputs, warnings}` — `status` normalized to
`processing|completed|failed|not_found` for the frontend polling loop.

## 4. Novice vs Expert flow (already supported)

- **Novice:** dropdown (`/api/technologies/frontend`) → upload (`/api/upload/sign` →
  `/api/dataset/upload`) → `POST /api/workflow/run` with defaults → poll
  `/api/jobs/{id}/status` → `GET .../spatial-data`.
- **Expert:** same, but `POST /api/workflow/run` accepts per-module params
  (normalization, clustering resolution, SVG `statistic`/`n_perms`/`fdr_alpha`, MBSI
  reconstruction params). The `technologies/frontend` entries expose
  `normalization`, `clustering`, `compatible_analyses` to populate expert controls.

## 5. What did NOT change
- SVG feature (separate patch) untouched.
- Existing `/api/*` routes and `main.py` verb-API unchanged.
- All additions are additive; 8/8 SVG tests + import smoke test still green.
