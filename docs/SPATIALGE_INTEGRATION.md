# spatialGE 2.x integration for MBSI Studio

MBSI Studio supports optional **execution of the upstream R package**
[FridleyLab/spatialGE](https://github.com/FridleyLab/spatialGE) via Rscript.
This is a bridge to original spatialGE methods, **not** an independent Python
reimplementation, and it does not copy or vendor upstream R source.

## Scope

The bridge currently exposes these spatialGE exports to MBSI users:

| spatialGE method | Use in MBSI |
| --- | --- |
| STclust | spatially weighted hierarchical tissue domains |
| SThet | Moran's I and Geary's C for each tissue |
| compare_SThet | across-tissue spatial heterogeneity plots |
| STdiff | within-tissue DE with optional spatial mixed models |
| STenrich | gene-set spatial enrichment and permutation tests |
| STgradient | distance-to-domain gene expression gradients |
| STniche | gene-set local Moran features and cross-tissue niches |
| plot_stniche | spatial niche visualizations |
| gene_interpolation, STplot_interpolation | kriging-based gene expression surfaces |
| STplot | gene and domain spatial maps |
| pseudobulk_samples, pseudobulk_dim_plot, pseudobulk_heatmap | sample-level exploratory aggregation and plots |
| transform_data, filter_data | upstream transformations and filtering |
| distribution_plots, plot_counts, summarize_STlist, get_gene_meta | QC, summaries and metadata |

The **Custom method sequence** control permits any function in
`SUPPORTED_OPERATIONS` with validated JSON options. Methods are executed
sequentially, with intermediate RDS and final STlist artifacts. The operator
must specify required method arguments (for example `annot` and `ref`
for STgradient, `gene_sets` for STenrich/STniche, or `annot` for STdiff).

Not all upstream exports are enabled: on-disk STlist storage, Seurat
conversion, image loaders, and internal-store validation need separate
filesystem and model compatibility testing before exposure.

## Install optional R backend

1. Install R (with `Rscript` on PATH) and system prerequisites.
2. In R, install `jsonlite`, `remotes` and spatialGE:

```r
install.packages(c("jsonlite", "remotes"))
remotes::install_github("FridleyLab/spatialGE")
stopifnot(packageVersion("spatialGE") >= "2.0.0")
```

spatialGE has extensive CRAN/Bioconductor and compiled dependencies; follow
its upstream installation documentation. MBSI does **not** silently install R.

## Use in Streamlit

Study & Data -> ingest one or more real spatial datasets ->
**Advanced spatialGE methods (optional R engine)**. Choose a preset or an
allowlisted custom JSON sequence, then run. The app writes one timestamp-free
unique output directory per run under `data/outputs/spatialge/`.

Example custom JSON:

```json
[
  {"method": "transform_data", "params": {"method": "log"}},
  {"method": "SThet", "params": {"genes": ["TP53", "CD3D"], "method": ["moran", "geary"]}},
  {"method": "compare_SThet", "params": {"genes": ["TP53", "CD3D"]}}
]
```

## Use programmatically

```python
from mbsi.integrations.spatialge import prepare_spatialge_inputs, run_spatialge

manifest = prepare_spatialge_inputs(
    {"tumor_01": tumor_adata, "control_01": control_adata},
    "data/outputs/spatialge/my_clean_run"
)
result = run_spatialge(manifest, [
    {"method": "transform_data", "params": {"method": "log"}},
    {"method": "SThet", "params": {"genes": ["TP53"], "method": ["moran", "geary"]}}
])
print(result["status"], result["version"])
```

## Compatibility and scientific constraints

- Input uses **real nonnegative integer raw counts**, genes x observations and
  finite x/y coordinates in `obsm["spatial"]`. If a validated `counts`
  layer exists, it is preferred over `X`.
- Existing nonmissing spot-level `cluster`, `leiden`, `cell_type`, or `domain` labels are exported into a separate TSV and strictly matched by observation barcode; no patient identifiers are exported by default. Custom STdiff/STgradient calls can reference these labels via their `annot` parameter.\n- Each sample has a separate counts/coordinates file; a stable generated
  `MB000001` alias prevents sample-name substring collisions in upstream
  file parsing. The manifest records original identifiers.
- This first bridge uses spatialGE's documented **tabular count interface**
  and writes dense TSV files. The default explicit limit is ten million
  gene-by-observation entries **per sample**. For large Visium HD/Xenium/CosMx,
  prefer upstream native output support or a future on-disk sparse adapter.
  The present bridge refuses oversized exports instead of silently exhausting
  memory.
- Coordinates are transferred as supplied, without pretending they are in
  microns or aligned across sections. Image overlays and image registration
  remain MBSI-native.
- SpatialGE's STdiff models spot-/cell-level contrasts within samples;
  their p-values must **not** be presented as replicate-aware case/control
  evidence. For biological group inference, use independent patient/sample
  units and a validated MBSI pseudobulk statistical model.
- Kriging surfaces are **interpolations**, not measured expression between
  locations. STniche assignments are inferred, not cell boundaries.
- Upstream result `*.rds`, final `spatialge_final_STlist.rds`,
  per-sample spatial metadata CSVs, and `summary.json` are preserved.
- Never upload patient identifiers or restricted data without appropriate
  authorization and storage controls. Files remain on the MBSI host.
- Python bridge tests check export and validation independently of R. Actual
  spatialGE R method correctness and platform compatibility require
  end-to-end tests with an installed R toolchain and real reference datasets.

## Attribution

Upstream spatialGE is licensed MIT (copyright Moffitt Cancer Center);
see its source [LICENSE](https://github.com/FridleyLab/spatialGE/blob/main/LICENSE)
and [DESCRIPTION](https://github.com/FridleyLab/spatialGE/blob/main/DESCRIPTION).
Cite the relevant upstream papers if spatialGE results are used:

- Ospina et al. (2022), *Bioinformatics*,
  https://doi.org/10.1093/bioinformatics/btac145
- Ospina et al. (2025), *Cancer Research*,
  https://doi.org/10.1158/0008-5472.CAN-24-2346
- For STdiff: Ospina et al. (2024), *Scientific Reports*,
  https://doi.org/10.1038/s41598-024-61758-0
