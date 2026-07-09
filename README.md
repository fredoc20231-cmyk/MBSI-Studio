# MBSI Studio

Physics-aware spatial biology platform for **Milestone 1**: ingest real Visium, Xenium, and generic h5ad/CSV data, run QC and spatial analysis, and export results.

Full workflow guide: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

## Milestone 1 scope (supported now)

| Platform | Ingest | QC | Segmentation | Spatial analysis | Export |
|----------|--------|----|--------------|------------------|--------|
| **10x Visium** | Yes | Yes | Yes | Yes | Yes |
| **10x Xenium** | Yes | Yes | Yes (boundaries / image) | Yes | Yes |
| **h5ad / CSV matrix** | Yes | Yes | Optional | Yes | Yes |

**Coming later (research / experimental):** CosMx, MERFISH, Stereo-seq, digital twin simulation, causal inference APIs, and other advanced modules. See [docs/RESEARCH_MODULES.md](docs/RESEARCH_MODULES.md).

## Quick start (local)

```bash
git clone https://github.com/fredoc20231-cmyk/MBSI-Studio.git
cd mbsi-studio
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# API (Milestone 1 / Builder contract on :8000)
./scripts/run_api.sh

# Streamlit SaaS UI (production — real uploads only)
SAFE=1 ./scripts/start_ui.sh

# Optional: labeled demos + reference cockpit (developer only)
DEVELOPER_MODE=true SAFE=1 ./scripts/start_ui.sh
```

Open:

- UI: http://127.0.0.1:8501
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health or `/api/health`

## Docker

```bash
docker compose up --build
```

- **API** launches `mbsi.api.app:app` (Milestone 1 routes under `/api/*`)
- **UI** on port 8501
- CORS defaults to local Streamlit origins; override with `MBSI_CORS_ORIGINS`

## Production vs developer mode

| Mode | How | Behavior |
|------|-----|----------|
| **Production** (default) | No env vars | Real upload → ingest → QC → visualization only |
| **Developer** | `DEVELOPER_MODE=true` | Demo loaders, synthetic dashboards, reference cockpit |

## Milestone 1 API (primary)

The supported API is `mbsi/api/app.py` (`create_app()`), started by `./scripts/run_api.sh` and Docker.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health`, `/api/health` | Health check |
| GET | `/api/technologies` | Supported platforms |
| POST | `/api/project/create` | Create project |
| POST | `/api/dataset/upload` | Upload dataset |
| POST | `/api/dataset/inspect` | Inspect dataset |
| GET | `/api/dataset/readiness` | Readiness score |
| POST | `/api/workflow/run` | Run workflow module |
| GET | `/api/workflow/status` | Workflow status |
| POST | `/api/report/generate` | Generate report |

Legacy endpoints (`/upload`, `/run-mbsi`, …) remain in `mbsi/api/main.py` for backward compatibility but are **not** the Docker default.

Configure CORS:

```bash
export MBSI_CORS_ORIGINS="http://localhost:8501,https://your-frontend.example.com"
```

## Streamlit workflow

The SaaS shell guides:

1. **Study & Data** — per-sample upload (Visium folder, Xenium bundle, h5ad)
2. **QC & Transformation**
3. **Segmentation & Registration** — real boundaries / StarDist / Cellpose
4. **Visualization** — histology overlay, spatial plots
5. **Report & Export**

## Testing

```bash
python scripts/smoke_test_launch_imports.py

# Lightweight CI-equivalent suite
pytest -m "not heavy and not integration" -q

# Full suite including heavy reconstruction/benchmark tests
pytest -q

# Only heavy tests
pytest -m heavy -q
```

Pytest markers: `unit`, `integration`, `heavy` (see `pyproject.toml`).

## Project layout

```
mbsi-studio/
├── app/                 # Streamlit SaaS UI + workspaces
├── mbsi/
│   ├── api/             # FastAPI (app.py = Milestone 1)
│   ├── io/              # Visium, Xenium, universal ingest
│   ├── segmentation/    # Real boundary / StarDist / Cellpose pipelines
│   ├── qc/              # QC modules
│   └── workflows/       # Orchestrated pipelines
├── docs/
│   ├── USER_GUIDE.md
│   └── RESEARCH_MODULES.md
├── scripts/
│   ├── run_api.sh
│   └── start_ui.sh
└── tests/
```

## Research / experimental modules

Modules such as `mbsi/foundation/`, `mbsi/digital_twin/`, and `mbsi/causal/` are **research-stage** — partially wired to legacy API routes or developer UI, not Milestone 1 production paths. Status details: [docs/RESEARCH_MODULES.md](docs/RESEARCH_MODULES.md).

## License

MIT License
