# MBSI Studio Explore — white spatial browser

The production SaaS shell now includes **Explore · Spatial Browser**, inspired by
the usability of interactive tissue viewers, with an original MBSI interface.

## Frontend

- White background, purple accents, responsive Streamlit workspace.
- Real sample selection and synchronized feature choice across tissue maps.
- WebGL scatter for observed spot/cell coordinates, categorical cluster/domain
  coloring, sample-local region selection, and sample comparison tiles.
- Sample summary panel and links to existing spatialGE, DE, gene-set, niche,
  gradient and domain analysis workspaces.
- No fake tissue images, masks, labels, expression values or p-values.
- Tissue histology is not yet integrated into the new browser canvas; existing
  Visualization workspace retains its histology overlay.

## Backend contract

`mbsi/visualization/browser_contract.py` defines the `BrowserDataset` protocol:

```python
samples() -> list[str]
genes() -> list[str]
features() -> list[str]
view(sample_id: str, feature: str) -> SpatialView
summary(feature: str) -> list[dict]
```

The initial `AnnDataBrowserAdapter` reads already-ingested real `AnnData`
from Streamlit session state. This boundary enables a future FastAPI,
on-disk SpatialData, R spatialGE or remote job-result adapter to replace
the in-memory adapter without changing plot widgets.

**Important limitations:** current rendering transfers per-sample point arrays
to the browser. Very large Visium HD / Xenium datasets require tiled
server-side level-of-detail, image pyramids, and downsampled viewport queries
before production-scale performance can be claimed. Linked lasso selection
is local to the main sample; it does not imply coordinate alignment between
different tissue sections. A minimum of Streamlit 1.35 is recommended for
Plotly selection events; older installations display plots without selection.

## Test

```bash
pytest tests/test_spatial_browser.py -q
streamlit run app/streamlit_app.py
```

Select **Explore · Spatial Browser** after uploading observed spatial data
in **Study & Data**.

## Next integration steps

1. Render real H&E/IF image pyramids with scale-factor and coordinate checks.
2. Add server-side spatial tile/viewport API and decimation for >1M points.
3. Link region selections to DE, niches, communication and export provenance.
4. Persist selection state in project workspaces and provide auditable
   cross-sample correspondence/registration only when explicitly computed.
5. Add browser visual-regression and real Visium/HD/Xenium acceptance tests.
