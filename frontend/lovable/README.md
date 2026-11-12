# Lovable launch — MBSI Studio Spatial Omics Intelligence

The MBSI scientific engine remains in this GitHub repository. A frontend builder
such as Lovable should create a **separate React application** and call the
FastAPI backend; do not try to run Python workflows in the Lovable browser.

## 1. Build from the specification
Copy [MASTER_PROMPT.md](MASTER_PROMPT.md) into a new Lovable project and ask it
to implement a real-data-first interface. Provide the API's OpenAPI schema
from `http://localhost:8000/openapi.json` when developing locally and the
typed client [mbsi-api.ts](mbsi-api.ts).

Lovable's GitHub integration may manage its own frontend repository; treat
this repository as the scientific backend source of truth. Connect the two
using HTTPS API calls and a separately deployed backend. Do not assume
arbitrary existing GitHub repository imports are supported.

## 2. Start the backend
```bash
git clone https://github.com/fredoc20231-cmyk/MBSI-Studio.git
cd MBSI-Studio
git fetch origin
git switch feature/comparative-spatial-testing-20261112
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest tests/test_frontend_v2_api.py tests/test_comparative_preview.py -q
MBSI_CORS_ORIGINS=http://localhost:5173,http://localhost:8501 ./scripts/run_api.sh
```
Visium, Xenium and H5AD ingest routes remain at `/api/dataset/upload`.
Compare real annotated H5AD datasets with `/api/v2/comparisons/preview`.
Try `http://localhost:8000/docs` for interactive OpenAPI documentation.

## 3. Frontend environment
For a Vite-based frontend, set:
```env
VITE_MBSI_API_BASE_URL=http://localhost:8000
```
Copy `mbsi-api.ts` into your frontend project under `src/lib/mbsi-api.ts`.
Install UI components and a WebGL plotting library. No API secret is required
for **local research-only mode**; public exposure of this backend must be blocked
until identity, authorization, request limits and data protection are implemented.

## 4. Acceptance checklist
- [ ] User uploads two real annotated H5AD tissue files.
- [ ] The API returns two unique dataset IDs and inspection metadata.
- [ ] Frontend displays sample units, genes, annotation categories and QC.
- [ ] Gene search and spatial maps retrieve source data without hardcoded values.
- [ ] The user selects compatible annotations and genes across samples.
- [ ] Comparison returns observed cell/spot proportions and gene mean differences.
- [ ] Similarity matrix, plots and warnings display and update interactively.
- [ ] Empty data, missing coordinates, unrecognized labels and failed uploads
      show actionable errors rather than fabricated results.
- [ ] User can download truthful descriptive results and provenance.
- [ ] Automated API and end-to-end browser tests pass.

## 5. Current constraints
This is a scientific preview, not a finished universal 10x HD workflow.
`/api/v2/datasets/{id}/spatial-points` returns up to 50,000 sampled points
rather than image tiles. Standard Space Ranger Visium uploads are the current
baseline; Visium HD segmented/bin-level import, automatic cluster harmonization,
replicate-aware statistical inference, and a tile server need additional
validated backend work.

Consult [COMPARATIVE_TESTING.md](../../docs/COMPARATIVE_TESTING.md) for
the existing Streamlit comparison UI and sample preparation requirements.
