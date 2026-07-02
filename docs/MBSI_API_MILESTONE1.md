# MBSI API — Milestone 1

Base URL (local): `http://127.0.0.1:8000`

Milestone 1 accepts only three functional platform hints: **`visium`**, **`xenium`**, **`generic_h5ad`** (aliases: `csv_matrix`, `h5ad`, `generic`). Other hints are rejected with a warning; detected non-milestone platforms receive compatibility status **`coming_later`**.

## Health

```
GET /health
```

Response includes `milestone_1_platforms: ["visium", "xenium", "generic_h5ad"]`.

## Technology catalog

```
GET /api/technologies
```

Returns all catalog entries with `milestone_status` (`active` | `coming_later`) and `milestone_1_functional` boolean.

## Project

```
POST /api/project/create
POST /api/project/update
```

Unchanged from core API — project metadata only.

## Dataset ingestion

```
POST /api/dataset/upload?project_id=&technology_hint=&sample_id=
  multipart: file
```

| `technology_hint` | Behavior |
|-------------------|----------|
| `visium` | Space Ranger outs / ZIP |
| `xenium` | Xenium outs / ZIP |
| `generic_h5ad` | h5ad or CSV+coords fallback |
| Other | Warning appended; hint ignored for ingestion routing |

Response fields: `dataset_id`, `platform`, `technology_profile`, `readiness`, `compatibility`, `warnings`, `summary`.

```
POST /api/dataset/inspect   { "dataset_id": "...", "source_path": "..." }
GET  /api/dataset/readiness?dataset_id=...
```

## Workflow modules (Milestone 1)

```
POST /api/workflow/run
```

| `module` | Pipeline stage |
|----------|------------------|
| `qc_transformation` | QC summary, filter, normalize |
| `visualization` | PCA, UMAP, spatial plots |
| `spatial_variable_genes` | Moran's I / SVG table |
| `spatial_domains` | Domain detection |
| `phenotyping` | Marker panel + TME scores |
| `report_export` | HTML / PDF / bundle |

Non-milestone datasets: compatibility matrix entries use status **`coming_later`** with reason *not in Milestone 1 scope*.

## Results & report

```
GET  /api/workflow/status?run_id=
GET  /api/results/list?dataset_id=
GET  /api/findings/list
GET  /api/evidence/list
POST /api/report/generate
```

## Compatibility matrix keys

Milestone modules exposed in `compatibility`:

- `study_data`
- `qc_transformation`
- `visualization`
- `spatial_variable_genes`
- `spatial_domains`
- `phenotyping`
- `report_export`

Legacy aliases: `upload`, `qc`, `spatial_analysis`, `report`.

Statuses: `available`, `warn`, `unavailable`, **`coming_later`** (non-milestone platforms).

## Example upload

```bash
curl -X POST "http://127.0.0.1:8000/api/dataset/upload?technology_hint=xenium&project_id=demo" \
  -F "file=@xenium_outs.zip"
```

## Example workflow

```bash
curl -X POST http://127.0.0.1:8000/api/workflow/run \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"<id>","module":"spatial_variable_genes","params":{"n_top":200}}'
```
