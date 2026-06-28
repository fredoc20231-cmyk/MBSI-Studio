# MBSI Studio — Cursor Development Instructions

## What This Project Is

**MBSI Studio** is a physics-aware spatial transcriptomics super-resolution platform. It takes
10x Visium spot-level data (low resolution, one RNA "blob" per 55 µm spot) and reconstructs
single-cell resolution gene expression using three interlocking physics engines:

1. **Anisotropic diffusion kernel** — anisotropic Gaussian derived from tissue morphology tensors
2. **Unbalanced optimal transport (OT)** — Sinkhorn algorithm with marginal relaxation (ρ₁, ρ₂)
3. **Sheaf Laplacian regularization** — graph regularizer that respects tissue compartment boundaries

The objective solved is:
```
min_{T, X}  OT_{ε,ρ}(a, b, T)  +  λ_sheaf · R_sheaf(X)
```

This is **not** a simple deep-learning model — every computation is interpretable biophysics.

---

## Repository Layout

```
mbsi-studio/
├── mbsi/                   # Core Python library (the science)
│   ├── diffusion/          # Kernels, PDE solvers, Green functions
│   ├── morphology/         # H&E image features → diffusion tensors
│   ├── segmentation/       # Tissue / nuclei / cell boundary segmentation
│   ├── sheaf/              # Graph builder + sheaf Laplacian regularizer
│   ├── reconstruction/     # Main solver (run_mbsi, run_iterative_mbsi)
│   ├── boundaries/         # Boundary leakage + invasion detection
│   ├── temporal/           # Multi-timepoint alignment + dynamics
│   ├── multimodal/         # ATAC, protein, mutation, clinical fusion
│   ├── digital_twin/       # In-silico perturbation simulator
│   ├── validation/         # Metrics suite (Pearson, RMSE, Moran's I, …)
│   ├── copilot.py          # AI Copilot: LLM-free template-based query answering
│   ├── guardrails.py       # Disclaimer banners / causal warning text
│   └── api/                # FastAPI backend (routes.py, routes_advanced.py)
├── app/                    # Streamlit UI
│   ├── streamlit_app.py    # Main dashboard cockpit (opens directly)
│   ├── style.css           # Full dark-theme CSS (edit this for all visual changes)
│   ├── components/         # Reusable Streamlit widgets
│   │   ├── layout.py       # inject_styles, render_navbar, render_subtabs, render_analysis_subtabs
│   │   ├── topnav.py       # render_topnav (button-row nav used by sub-pages)
│   │   ├── statusbar.py    # Fixed bottom status bar
│   │   ├── page_utils.py   # init_session, guardrail_banner, ensure_adata, …
│   │   ├── cards.py        # Metric strip, donut, pseudotime, causal, invasion, treatment radar
│   │   ├── histology.py    # Plotly histology overlay, marker heatmap, ligand gradient
│   │   ├── network.py      # Neighborhood graph + interactions bar
│   │   ├── tables.py       # Pathway table renderer
│   │   ├── plots.py        # General-purpose plot helpers
│   │   ├── uploaders.py    # upload_panel, data_readiness_score
│   │   ├── parameter_panels.py  # mbsi_parameter_panel, run_mode_selector
│   │   ├── demo_data.py    # generate_dashboard_demo (pure synthetic, no files needed)
│   │   └── report_builder.py    # HTML/PDF report generation
│   └── pages/              # Streamlit multi-page files (numbered prefix = nav order)
│       ├── 01_Dashboard.py  → redirects to streamlit_app.py cockpit
│       ├── 02_Upload_Data.py
│       ├── 03_Preprocess.py
│       ├── 04_Segmentation.py
│       ├── 05_Run_MBSI.py
│       ├── 06_Analysis.py   → redirects to streamlit_app.py
│       ├── 07_Validation.py
│       ├── 08_AI_Copilot.py
│       └── 09_Export.py
├── scripts/                # CLI entry points (run_demo, run_benchmark, …)
├── tests/                  # pytest suite
├── data/
│   ├── demo/               # Pre-generated demo outputs (h5ad, metrics.json, figures/)
│   └── demo/advanced/      # Advanced demo state (analysis_state.json)
├── Dockerfile
└── docker-compose.yml      # Runs Streamlit :8501 + FastAPI :8000
```

---

## Running the App

```bash
# Quick local start
streamlit run app/streamlit_app.py

# Or with Docker
docker compose up --build
# Streamlit → http://localhost:8501
# FastAPI   → http://localhost:8000/docs
```

---

## Architecture Principles

### Data Flow

```
User uploads h5ad / Visium folder
        ↓
st.session_state.adata  (AnnData, spots × genes)
        ↓  Preprocess page (QC, HVG selection)
        ↓  Segmentation page (tissue mask, Voronoi / nuclei)
        ↓  Run MBSI page → mbsi.reconstruction.solver.run_mbsi()
st.session_state.reconstructed  (AnnData, cells × genes)
        ↓  Validation page → mbsi.validation.run_validation_suite()
st.session_state.metrics  (dict of floats)
        ↓  Analysis / Dashboard / AI Copilot
```

### Session State Keys (never rename these without grep-searching all pages)

| Key | Type | Set by |
|-----|------|--------|
| `adata` | AnnData | Upload / demo loader |
| `reconstructed` | AnnData | Run MBSI |
| `true_adata` | AnnData | Upload (ground truth) |
| `metrics` | dict | Validation |
| `analysis_state` | dict | Advanced demo / Analysis |
| `spatial_demo` | dict | generate_dashboard_demo |
| `uploaded_image` | np.ndarray | Upload |
| `segmentation_result` | dict | Segmentation |
| `boundaries_result` | dict | Boundaries analysis |
| `digital_twin` | dict | Digital twin simulation |
| `using_synthetic_demo` | bool | Demo loader |
| `last_run` | str | Any action button |

### AnnData Contract

```python
adata.X                  # float32 CSR matrix, spots × genes
adata.obsm['spatial']    # float64 array, shape (n_spots, 2), µm units
adata.var_names          # gene symbols
adata.obs_names          # spot barcodes / cell IDs
adata.obs['cell_type']   # optional, used by composition plots
```

---

## CSS & Visual System

All styling lives in `app/style.css`. CSS variables in `:root`:

```css
--bg: #07111f       /* app background */
--panel: #0d1828    /* card/panel background */
--panel2: #101d2e   /* secondary panel */
--border: #22314a   /* borders */
--text: #f4f7fb     /* primary text */
--muted: #9aa7b8    /* secondary text */
--blue: #4f7cff     /* primary accent */
--green: #39d98a    /* success / positive */
--orange: #ffb020   /* warning */
--red: #ff5c7a      /* error / high */
--purple: #9b6cff   /* AI / copilot accent */
--cyan: #30d5c8     /* physics / diffusion accent */
--pink: #ff5c9c     /* multimodal accent */
```

Key CSS classes: `.mbsi-panel`, `.mbsi-panel-title`, `.mbsi-panel-heading`,
`.mbsi-navbar`, `.mbsi-nav-item.active`, `.mbsi-subtab.active`,
`.mbsi-legend-dot`, `.mbsi-legend-item`, `.mbsi-accent-purple`.

**Do not** inline long style strings in Python — add a class to `style.css` instead.

---

## What Needs to Be Built / Improved

### Priority 1 — Make Navigation Interactive (Current Gap)

The top navbar in `streamlit_app.py` uses `render_navbar()` from `layout.py`, which renders
**static HTML** — the nav items are not clickable buttons. Only `render_topnav()` (used by
sub-pages) uses real Streamlit buttons.

**Task**: Replace `render_navbar()` in `streamlit_app.py` with `render_topnav()` so the main
cockpit's nav links actually navigate. Or wire `render_analysis_subtabs()` so the subtab row
at the top of the cockpit switches content sections in-place (cell types, clusters, etc.).

### Priority 2 — Subtab Content in Main Cockpit

`streamlit_app.py` has a static `render_subtabs()` row (Spatial Map / Cell Types / Clusters /
Neighborhoods / Boundaries / Pathways / 3D View). The helper `render_analysis_subtabs()` in
`layout.py` already implements a clickable version that returns the active tab name.

**Task**: Replace `render_subtabs(active="Spatial Map")` in `streamlit_app.py` with
`active_tab = render_analysis_subtabs()`. Then gate the center column's content with
`if active_tab == "Spatial Map": ... elif active_tab == "Cell Types": ...` etc.

Each subtab should show a relevant Plotly figure from `demo_data.py` / `histology.py`.

### Priority 3 — Upload Page UX

`app/pages/02_Upload_Data.py` currently shows `st.scatter_chart()` (basic Streamlit chart)
for the spatial preview. Replace with a proper `make_histology_overlay()` from
`app/components/histology.py` — pass the uploaded image and a mock cell DataFrame derived
from `adata.obsm['spatial']`.

Also wire the "Load Advanced Demo" button to call `load_advanced_demo_into_session(force=True)`
and then `st.switch_page("streamlit_app.py")` so the user lands on the cockpit with data loaded.

### Priority 4 — Run MBSI Progress

`app/pages/05_Run_MBSI.py` wraps `run_mbsi()` in a single `st.spinner()`. Add an `st.progress()`
bar that increments based on the `convergence_log` returned by `run_iterative_mbsi`. The solver
returns `adata_out` with `adata_out.uns['convergence_log']` as a list of per-iteration dicts.

```python
log = st.session_state.reconstructed.uns.get('convergence_log', [])
```

Render the convergence curve as `st.line_chart({'OT loss': [e['ot_loss'] for e in log]})`.

### Priority 5 — Validation Page Metrics Display

`app/pages/07_Validation.py` shows raw metrics in `st.bar_chart()`. Replace with the
`metric_tile()` helper from `app/components/layout.py` and add a radar chart (reuse
`treatment_radar()` from `app/components/cards.py` but feed validation metric groups).

Key metric groups to display:
- **Reconstruction quality**: `pearson_r`, `spearman_r`, `rmse`
- **Spatial structure**: `morans_i_pearson`, `marker_loc_score`
- **Boundary fidelity**: `boundary_leakage_score`
- **Classification**: `cell_type_accuracy`

### Priority 6 — AI Copilot Enhancement

`app/pages/08_AI_Copilot.py` calls `mbsi.copilot.answer_tissue_query()`. Currently answers
are returned as plain text. Improve the display:
1. Parse any `**bold**` / `- list` markdown and render with `st.markdown()` instead of the
   `div` wrapper.
2. Add a "Copy" button using `st.code(answer, language=None)` as an alternative display.
3. Show a "Confidence" badge (from the returned dict if it has a `confidence` key).

### Priority 7 — Export Page

`app/pages/09_Export.py` should offer three export options:
1. **HTML report** — call `mbsi.visualization.report.generate_html_report()`
2. **PDF summary** — via `matplotlib` (already imported in `app/components/report_builder.py`)
3. **Data bundle** — zip of `reconstructed.h5ad` + `metrics.json` + figures

Use `st.download_button()` for each. Files should be written to `data/outputs/` first.

### Priority 8 — FastAPI Integration Status

`app/components/page_utils.py` has `check_backend_online()` but it is never displayed.
Add a backend health indicator in `render_statusbar()` inside `app/components/statusbar.py`:
green dot if `check_backend_online()` returns True, red dot otherwise. Cache the check
result in `st.session_state.backend_online` with a 30-second TTL.

---

## Coding Conventions

- **Python 3.11**, type hints encouraged but not required
- **Imports**: stdlib → third-party → `mbsi.*` → `app.*`; no wildcard imports
- **No comments** unless the WHY is non-obvious (physics invariants, workarounds)
- **Plotly** for all interactive charts; `matplotlib` only for static PDF export
- **Dark-theme first**: every new chart should set `paper_bgcolor='rgba(0,0,0,0)'`,
  `plot_bgcolor='rgba(0,0,0,0)'`, `font_color='#f4f7fb'`
- **No st.sidebar** — sidebar is hidden globally in CSS (`display:none`)
- **st.session_state** mutations must go through `init_session()` defaults — add new keys
  there before using them anywhere else
- Line length: 100 chars (Black-compatible)

---

## Testing

```bash
# Full suite
pytest tests/ -x -q

# Fast subset (no heavy reconstruction)
pytest tests/test_kernel.py tests/test_sheaf.py tests/test_segmentation.py -q

# Coverage
pytest --cov=mbsi tests/ --cov-report=term-missing
```

New features need a test in `tests/test_<module>.py`. Mock `adata` with:

```python
import anndata as ad, numpy as np, scipy.sparse as sp
def make_mock_adata(n_spots=20, n_genes=10):
    X = sp.random(n_spots, n_genes, density=0.5, format='csr', dtype=np.float32)
    coords = np.random.rand(n_spots, 2) * 1000
    return ad.AnnData(X=X, obsm={'spatial': coords})
```

---

## Key Entry Points for Common Tasks

| Task | File(s) to edit |
|------|----------------|
| Change dashboard layout | `app/streamlit_app.py` |
| Add a new chart type | `app/components/cards.py` or `histology.py` |
| Modify OT solver parameters | `mbsi/reconstruction/solver.py` |
| Add a new validation metric | `mbsi/validation/metrics.py` |
| Add a new API endpoint | `mbsi/api/routes.py` + `routes_advanced.py` |
| Change visual theme | `app/style.css` |
| Add a new page | `app/pages/NN_Name.py` + register in `topnav.py` NAV_PAGES |
| Change demo data | `app/components/demo_data.py` + `generate_dashboard_demo()` |
| Extend session state | `app/components/page_utils.py` → `init_session()` |
| Add copilot query template | `mbsi/copilot.py` → `QUERY_TEMPLATES` |

---

## Do Not

- Do **not** add `st.sidebar` widgets — sidebar is hidden globally
- Do **not** add real LLM API calls to `copilot.py` without a feature flag + guardrail banner
- Do **not** remove `guardrail_banner()` from any page — required legal/scientific disclaimer
- Do **not** change `adata.obsm['spatial']` key name — hardcoded throughout the codebase
- Do **not** break the `generate_dashboard_demo()` interface — it's the fallback for demo mode
- Do **not** create new CSS files — append to `app/style.css`
