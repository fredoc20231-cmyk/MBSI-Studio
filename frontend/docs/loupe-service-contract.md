# Loupe integration: backend handoff

## Status and source inspection

The uploaded `loupeR-main.zip` contains **loupeR 1.1.5**, an R library with **15 public exports**, not a browser application. Its source, binaries, test data, and vendor logo are **not redistributed** in this frontend. The archive contains no database, authentication system, records, hosted endpoints, callback handlers or schedules. Existing MBSI ownership, storage, API and deployment remain authoritative.

The frontend `/loupe` workspace and the following **proposed v1 contract** are implemented. These endpoints are not claimed to exist in MBSI today. Missing endpoints, dependencies or license readiness leave actions unavailable. UI fixtures validate integration behavior, not scientific correctness or real file compatibility.

## Runtime choice and license gate

Retain the official R implementation behind the existing FastAPI service, rather than translating scientific behavior or reverse-engineering `.cloupe`. The external backend team should invoke a preinstalled R worker through a controlled job adapter. This work changes **no scientific Python**.

The supplied LICENSE permits internal use in connection with qualifying 10x products/data and prohibits redistribution or sublicensing of the software and derivatives. The service owner must review the intended hosted use with the vendor before activation; possession of the ZIP is not approval. Install the official library and Louper through authorized channels. Do not accept an EULA automatically or treat a checkbox in this UI as vendor license acceptance.

Required runtime: R >= 4.0.0, Seurat, hdf5r, native HDF5, and the official Louper executable. Matrix/SeuratObject support depends on the input; BPCells is needed for IterableMatrix. Source setup references Louper 1.1.5 and verifies its vendor digest. Keep downloads/setup outside user jobs. No GitHub token is requested by the frontend. Report actual installed versions, not expected versions.

## Coverage

| Function | UI | Service responsibility |
|---|---|---|
| create_loupe_from_seurat | Export: Seurat → Loupe | Load an authorized Seurat object; select counts, metadata clusters and 2D reductions; official conversion |
| create_loupe | Export: Counts → Loupe | Resolve counts/categories/projections for the selected dataset; validate and convert |
| create_hdf5 | Export: HDF5 interchange | Validate inputs and create the library-compatible interchange file |
| select_assay | Checks & utilities | Report actual usable assay; default priority is active, RNA, then others |
| counts_matrix_from_assay | Checks & utilities | Resolve assay counts without substituting normalized expression; return artifact/summary |
| select_clusters | Checks & utilities | Factor/character metadata and active identity; optional metadata columns and deduplication |
| select_projections | Checks & utilities | Only observed two-dimensional reductions; no browser-generated embeddings |
| read_feature_ids_from_tsv | Checks & utilities | Resolve an authorized uploaded features TSV(.gz); use first-column IDs, preserve feature ordering |
| validate_count_mat | Checks & utilities | Sparse type, dimnames, finite values, barcode and feature-ID requirements |
| validate_barcodes | Checks & utilities | Official library barcode rules, including permitted assay-specific formats |
| validate_clusters | Checks & utilities | Named factors, barcode-length alignment, nonempty levels and <=32768 groupings |
| validate_projections | Checks & utilities | Named finite matrices with barcode count rows and exactly two columns |
| create_bugreport | Checks & utilities | Diagnostic text; warn it can contain sampled feature names and cell barcodes |
| create_bugreport_from_seurat | Checks & utilities | Seurat diagnostics with actual versions and selections |
| setup | Checks & utilities: administrator-managed | Authorized service installation/license workflow; never execute via the public job endpoint |

PNG/SVG generation is **not** a loupeR export. The optional `render_projection` operation uses a separate backend renderer and observed projections/overlays. It must independently report availability and supported image formats. The library partially supports Visium/Xenium expression; **it cannot embed/export their tissue images**. Full spatial tissue-image output needs a separately supported backend pipeline. `.cloupe` creation does not provide an embeddable Loupe Browser UI or all interactive Loupe Browser analyses.

## Proposed endpoints

All endpoints share `VITE_MBSI_API_URL` / the validated tab-scoped scientific-service override. Enforce the existing service's authentication and dataset ownership on **every** read, job, status and artifact. If authenticated transport is needed, it must be integrated with that service's established session contract before deployment; this adapter does not invent auth or use workspace GitHub credentials. Allow only the actual frontend origins through CORS.

### GET /api/loupe/capabilities

```json
{
  "contract_version": 1,
  "runtime": {"r": null, "loupeR": null, "hdf5": null, "louper": null, "license_ready": false},
  "operations": [],
  "image_formats": []
}
```

Return actual runtime values and `operations` entries of `{ "function": "create_loupe", "available": false, "reason": "Official converter not installed" }`. The empty example represents unavailability, not a seeded runtime. An installed library is insufficient proof of license eligibility. `available` also means the service can resolve the necessary supported input representation. Setup remains administrator-managed regardless of its capability flag.

### POST /api/loupe/run

Body: `{dataset_id, function, params, allow_demo:false}`. The frontend rechecks capabilities immediately before each submission and never intentionally requests demo execution. Backend must independently reject demo, unknown functions, unsupported inputs and unauthorized dataset IDs.

Supported UI parameters: `output_name` (basename only), `metadata_cols` (optional comma-separated keys converted to an array), `dedup_clusters` (boolean), `projection_names` (optional keys), `features_dataset_id` (optional authorized upload). These are **adapter parameters**, not all literal R function arguments: map `dedup_clusters` to `dedup` for select_clusters, resolve feature IDs server-side, and apply projection selection without changing ordering. Do not pass arbitrary client keys directly to R.

Image-only parameters: `format` (`png`/`svg`), `gene`, `width`, `height`. Resolve gene and projection names against observed data; reject unavailable overlays instead of filling them. The browser imposes 100–8000 px per dimension; backend must impose its own resource limits.

Server owns `output_dir`, `h5path`, `executable_path`, R object versions, assay resolution and temporary paths. Generate isolated per-run directories, never accept filesystem paths from the browser, and do not overwrite existing artifacts (`force:false`). Use an explicit operation allowlist and argument arrays, not interpolated shell commands. Validate dimensions, ordering and type with the library; do not calculate or translate scientific validation in the browser.

Return a run object:

```text
{
  id: string,
  dataset_id: string,
  function: string,
  status: "queued" | "running" | "completed" | "blocked" | "failed",
  outputs: object,
  warnings: string[],
  artifacts: [{id, name, kind, mime_type}],
  error?: string
}
```

Artifact kind: `cloupe`, `hdf5`, `image`, `report`, or `table`. Do not invent artifacts when the underlying R call returns TRUE; verify actual file existence and integrity first. `outputs` includes observed selections, validation responses and provenance (tool/runtime versions, parameters, source dataset identity, checksums and warnings). Capture diagnostics safely; they may contain sensitive cell identifiers. Don't return full server paths or credentials.

### GET /api/loupe/status?run_id=...

Return the same run schema. Frontend polls queued/running jobs every two seconds; terminal results stop polling. Validate run ownership and ensure IDs stay tied to the dataset. Report failures explicitly.

### GET /api/loupe/runs?dataset_id=...

Return an array of authorized persisted runs using the schema above. Empty array means no observed runs. The UI checks returned dataset IDs and scopes cache keys by scientific service and dataset. Reload retrieves actual service records rather than browser-fabricated history.

### GET /api/loupe/artifacts/{encoded-id}

Stream authorized artifact bytes with correct Content-Type and Content-Disposition; serve PNG as image/png and SVG as image/svg+xml. Artifact IDs are opaque, not file paths. Resolve through an ownership-checked artifact registry, prevent traversal, and escape plot labels. Return downloadable `.cloupe`, `.h5`, diagnostics and tables from actual worker outputs only. Frontend previews returned image bytes and never fetches arbitrary URLs supplied in a result.

## Deployment and verification still required

1. Service owner confirms licensing and installs the official R/converter runtime.
2. Backend team implements this contract, Seurat/TSV input retention and authorized observed-data image rendering without altering science from Lovable.
3. Provide the running HTTPS scientific-service address and allow frontend origins.
4. With a permitted real dataset, exercise import, each supported utility, conversion, terminal status readback and artifact download; open the generated `.cloupe` in a compatible official Loupe Browser.
5. Verify representative feature/cluster/projection alignment, PNG/SVG rendering, failure behavior, provenance, restart persistence and cross-user isolation. Remove test artifacts after verification.

Do not mark live conversion, image generation or migration complete before these checks. No backend runtime or license acceptance is supplied by this frontend PR.