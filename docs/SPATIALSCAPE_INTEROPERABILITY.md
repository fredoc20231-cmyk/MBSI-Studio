# SpatialScape interoperability and linked MBSI atlas

Reference: [MicTott/spatialscape](https://github.com/MicTott/spatialscape), tagged source archive v1.0.0 reviewed November 2026.
SpatialScape is MIT licensed, Copyright (c) 2026 Michael Totty.
Citation: Totty, M. (2026). *spatialscape: a static, reactive browser for spatial transcriptomics*.
[DOI 10.5281/zenodo.24376035](https://doi.org/10.5281/zenodo.24376035).

## Why integrate rather than replace

SpatialScape is a highly performant static spatial atlas viewer: sharded Zarr v3 gene-major
quantization, WebGL/deck.gl, linked snRNA-seq and ATAC, molecule and shape overlays,
selection, view URL state, and static hosting. MBSI's scientific and product
requirements differ: authenticated multi-tenant workspaces, provenance, validated
reconstruction, multi-sample analysis and interpretation. Replacing Lovable's
React/TanStack workspace with another SPA is not the right integration.

## Working changes in this branch

- **Lovable Compare → Linked tissue atlas**: synchronized gene/annotation selection,
  a consistent observed-value color range across selected samples, display threshold,
  sample-specific tissue maps and user-drawn polygon ROI.
- **POST /api/v1/datasets/{dataset_id}/selection**: exact selected
  spot/cell count, mean, median and detection rate for observed gene expression,
  or annotation category counts, with at most 5000 displayed barcode IDs.
  Calculated on the **full observed dataset**, not its sampled visualization.
  ROI is limited to 500,000 candidate rows per synchronous request.
- **Offline SpatialScape export**: prepare a dataset YAML from server-ingested AnnData
  and optionally run the *installed* upstream SpatialScape v1.0.0 builder and validator.
  This yields a native high-resolution, multi-section static viewer bundle without
  duplicating upstream internals inside MBSI's Render API.

Example (local research files only):

```bash
python -m pip install spatialscape==1.0.0
python scripts/export_spatialscape_bundle.py SAMPLE_DATASET_ID \
  --out ./private_atlas_export --already-microns --build

# For Visium source coordinates in pixels, provide measured calibration instead:
python scripts/export_spatialscape_bundle.py SAMPLE_DATASET_ID_1 SAMPLE_DATASET_ID_2 \
  --out ./private_atlas_export --microns-per-unit 0.45 --build

spatialscape serve ./private_atlas_export/bundles --open
```

For a separately secured, HTTPS-hosted static atlas, the Lovable frontend can show
an optional **Open high-resolution SpatialScape atlas** link. Configure its
build-time variable `VITE_MBSI_SPATIALSCAPE_URL=https://your-private-atlas.example`
and rebuild/republish the frontend. Local development additionally accepts
`http://localhost:<port>` or `http://127.0.0.1:<port>`; production intentionally
requires HTTPS. The link does not automatically grant permissions to the bundle,
nor authenticate users to an external host.

The number **0.45** above is an *illustrative placeholder only*, not a recommended
Visium calibration. Get the actual microns-per-source-unit from the image/Space Ranger
spatial calibration for those slides. Never mix samples with incompatible coordinate
units under one global scale argument.

The bundle exporter requires explicit unit confirmation and allows only
`cluster`, `leiden`, `domain`, `cell_type`, `niche`, and `condition`
observation fields to avoid dumping arbitrary metadata. It does not export
clinical demographics or automatically insert unreviewed annotations.
Source h5ad still contains all data and **must be controlled separately**.

## Scope and limitations

| Capability | Status |
|---|---|
| Linked spatial feature maps for up to 4 samples within Lovable | Implemented, sampled scatter |
| Exact server-side polygon selection and descriptive ROI stats | Implemented, bounded |
| Private SpatialScape static atlas bundle generation | Optional offline adapter |
| Multi-million-cell WebGL / sharded Zarr view | Provided by *external* SpatialScape viewer after validated bundle export, not embedded in Lovable |
| Histology pyramids, molecule and cell-boundary overlays | Supported by upstream SpatialScape when present in its correctly configured source; not auto-exported by this MBSI adapter |
| Linked ATAC and snRNA-seq reference embeddings | Supported upstream when specified in bundle YAML; not auto-configured here |
| Replicate-aware differential expression, causal inference, reconstruction validation | Distinct MBSI research/statistical workflows; not provided by this feature |
| Sample-to-sample tissue registration | **Not** performed; each sample retains its own native coordinate frame |
| HIPAA-ready hosted data sharing | **Not** provided; current public API must not receive patient-identifiable data |

## Test and release gates

The GitHub CI Python suite checks exact ROI statistics/invalid inputs and exporter
configuration; frontend CI must run both Vitest and Vite build. Confirm a real
dataset's gene names, source coordinate units, CORS/network access and domain
publication permissions before deployment. Browser rendering of downsampled
points should never be interpreted as full-resolution molecular evidence.

**License choice**: This MBSI integration independently implements the linked
viewer features and invokes SpatialScape as an optional separately installed
MIT-licensed package; it does not copy the upstream React/deck.gl viewer source.
Preserve its MIT copyright and citation when distributing generated viewers.
