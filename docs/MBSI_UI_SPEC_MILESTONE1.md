# MBSI UI Spec — Milestone 1

Authority for Milestone 1 UI scope gating (replaces missing `MBSI_UI_SPEC.md` for this release).

## Technology selector (Study & Data)

**Functional (selectable):**

1. 10x Visium (`visium`)
2. 10x Xenium (`xenium`)
3. Generic AnnData / CSV (`generic_h5ad`)

**Coming later (not selectable):**

- 10x Visium HD, MERFISH/MERSCOPE, NanoString CosMx, STOmics Stereo-seq, CODEX, Slide-seq, Spatial ATAC

Display rules:

- Active platforms in the primary `selectbox` labeled *Spatial technology (Milestone 1)*.
- Coming later platforms listed below in gray (`#888`) text: **Coming later:** … — not selectable in Milestone 1.
- Do not show coming-later platforms as supported workflows in compatibility tables or navigation CTAs.

## Xenium upload checklist

When Xenium is selected, show in Study & Data / upload section **before** upload tabs:

**Required:**

- `cell_feature_matrix.h5`
- `cells.csv.gz` or `cells.parquet`

**Optional:**

- `transcripts.parquet`
- `cell_boundaries.parquet`
- Morphology image

## Upload tabs

| Tab | Milestone 1 |
|-----|-------------|
| h5ad | Active (generic) |
| Visium ZIP | Active |
| Xenium ZIP | Active |
| Stereo-seq ZIP | Info banner: Coming later — no uploader |
| CSV Matrix + Coordinates | Active (generic fallback) |
| Image / Segmentation | Optional multimodal |

## Workspace gating

If session platform is not milestone-functional (`is_milestone_platform` false):

- **QC & Transformation**, **Visualization**, **Report & Export**: show warning and return early.
- Compatibility matrix: status `coming_later` with explanatory reason.

## Pipeline navigation (Milestone 1)

Study Setup → QC & Transformation → Visualization → Spatial Variable Genes → Spatial Domains → Phenotyping → Report & Export

Modules outside this path (Segmentation, Reconstruction, Benchmark, Discovery) remain in nav but are not Milestone 1 deliverables.

## Layout

No layout redesign — scope gating only via selector, captions, warnings, and disabled upload paths.
