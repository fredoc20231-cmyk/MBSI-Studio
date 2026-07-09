# Research & Experimental Modules

This document triages modules that are **not** part of Milestone 1 production scope. Nothing here is deleted — status labels clarify what is wired, what is research-stage, and what is safe to ignore for Visium/Xenium/h5ad workflows.

**Legend**

| Label | Meaning |
|-------|---------|
| **Production** | Wired to Milestone 1 UI/API and covered by lightweight CI |
| **Experimental** | Callable code exists; partial UI/API wiring; not Milestone 1 |
| **Research** | Algorithm prototypes; no production guarantees |
| **Legacy API** | Exposed only via `mbsi/api/main.py` legacy routes |
| **Developer UI** | Visible only with `DEVELOPER_MODE=true` or legacy Streamlit pages |

---

## Milestone 1 (production)

| Module | Status | Wired to |
|--------|--------|----------|
| `mbsi/io/` | Production | Study & Data upload, `/api/dataset/*` |
| `mbsi/qc/` | Production | QC workspace, ingest readiness |
| `mbsi/segmentation/` | Production | Segmentation workspace, Xenium boundaries |
| `mbsi/spatial_stats/` | Production | Visualization, QC |
| `mbsi/workflows/` | Production | Start Analysis pipeline |
| `mbsi/api/app.py` | Production | `./scripts/run_api.sh`, Docker |
| `mbsi/registry/` | Production | Project/dataset registry |
| `mbsi/reports/` | Production | Report & Export workspace |

---

## Research-stage (keep, do not delete)

### `mbsi/foundation/` — **Research**

- **Purpose:** Tissue embeddings, zero-shot region annotation, missing-gene prediction.
- **UI:** Not in Milestone 1 SaaS shell.
- **API:** Not in `mbsi/api/app.py`.
- **Notes:** Prototype for future foundation-model integration.

### `mbsi/digital_twin/` — **Experimental / Legacy API**

- **Purpose:** Tissue state model, treatment simulation scenarios.
- **UI:** Developer dashboard cards; legacy Streamlit export previews.
- **API:** `POST /digital-twin/*` on legacy `mbsi/api/main.py` only.
- **Notes:** Computational hypothesis only — not clinical simulation.

### `mbsi/causal/` — **Experimental / Legacy API**

- **Purpose:** Spatial causal DAG, interventions, driver ranking.
- **UI:** Discovery workspace (partial); legacy Analysis pages.
- **API:** `POST /causal/*` on legacy API.
- **Notes:** Research-stage causal inference — not validated causality.

### `mbsi/temporal/` — **Research / Legacy API**

- **Purpose:** Multi-timepoint alignment, dynamics, future-state simulator.
- **UI:** Not in Milestone 1 shell.
- **API:** `POST /temporal/*` on legacy API.
- **Notes:** `simulate_tissue_future` is a research simulator, not production forecasting.

### `mbsi/multimodal/` — **Research / Legacy API**

- **Purpose:** Fuse RNA + image + protein/ATAC/clinical features.
- **UI:** Not in Milestone 1 shell.
- **API:** `POST /multimodal/*` on legacy API.

### `mbsi/showcase/` — **Developer UI only**

- **Purpose:** HGSOC integrated demonstration pipeline (synthetic showcase data).
- **UI:** `pages/13_Ovarian_Cancer_Showcase.py` — blocked unless `DEVELOPER_MODE=true`.
- **API:** None in Milestone 1 contract.

### `mbsi/communication/` — **Experimental**

- **Purpose:** Ligand–receptor spatial signaling analysis.
- **UI:** Discovery workspace + legacy Communication Intelligence page.
- **API:** Legacy routes; workflow handler when real `adata` present.
- **Notes:** Uses session data in production; demo adata only in developer mode.

### `mbsi/tme/` — **Experimental**

- **Purpose:** Tumor microenvironment niche detection.
- **UI:** Discovery workspace + legacy TME Intelligence page.
- **API:** Legacy routes; workflow handler when real `adata` present.

### `mbsi/copilot/` — **Experimental**

- **Purpose:** Query grounded answers from computed session state.
- **UI:** AI Review workspace; legacy AI Copilot page.
- **API:** Legacy `/copilot` route.

### `mbsi/ml_learning/` — **Research**

- **Purpose:** ML learning run logging experiments.
- **UI:** Not wired to Milestone 1 shell.
- **API:** None.

### `mbsi/demo/` — **Developer only**

- **Purpose:** Synthetic spatial demo datasets for UI QA.
- **UI/API:** Gated behind `DEVELOPER_MODE=true`; blocked in production.

---

## Legacy API surface (`mbsi/api/main.py`)

Still importable for backward compatibility but **not** started by Docker or `./scripts/run_api.sh`:

- `/upload`, `/run-mbsi`, `/validate`, `/benchmark`, `/download/{job_id}`
- Advanced routes: segmentation, subcellular, boundaries, communication, causal, temporal, digital twin, multimodal, copilot

Use `mbsi/api/app.py` for all new integrations.

---

## Recommended usage

| Goal | Use |
|------|-----|
| Visium / Xenium / h5ad analysis | Milestone 1 UI + `mbsi/api/app.py` |
| Try causal / digital twin prototypes | Legacy API or `DEVELOPER_MODE=true` pages |
| Foundation model experiments | Import `mbsi/foundation/` directly in notebooks |
| UI QA with synthetic data | `DEVELOPER_MODE=true` |

When in doubt, follow [USER_GUIDE.md](USER_GUIDE.md) and stay on Milestone 1 paths.
