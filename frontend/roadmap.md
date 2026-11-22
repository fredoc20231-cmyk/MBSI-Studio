# MBSI Studio

## Upload connection and .cloupe viewing

- [x] Keep the deployed Render address available when a hosted build has no environment setting; 19 focused tests pass and the browser shows the Render default.
- [x] Allow explicit .cloupe file selection and expose the reader limitation without claiming a file was decoded; live browser failure verified with no runtime errors.
- [ ] Verify live browser uploads: blocked until Render allows the frontend origins through MBSI_CORS_ORIGINS.
- [ ] Read and visualize .cloupe contents: blocked on an authorized reader and observed-data viewing contract in the external scientific service; deployed OpenAPI has no Loupe endpoints.

## Loupe integration

- [x] Inspect uploaded loupeR 1.1.5: all 15 exports, dependencies, validation, license and image limitations.
- [x] Add the Loupe workspace, capability-gated external API adapter, configuration, outcomes and artifact views.
- [x] Test function availability, request integrity, service changes, downloads and compact layout: 27 tests passed; controlled browser fixtures verified, not live conversion.
- [x] Publish frontend-only changes to the existing repository in separate PR #15: https://github.com/fredoc20231-cmyk/MBSI-Studio/pull/15; all 620 non-frontend tree entries unchanged.
- [ ] Execute real Loupe conversion and image generation: blocked on the backend team's licensed R/Louper integration, observed-data renderer and deployed HTTPS service.

## Reference interface

- [x] Rebuild the shared workspace, Explore canvas, controls and analysis dock from the supplied reference.
- [x] Apply the new visual system to Analyze, Compare, Integrate, Annotation, Imaging and Reports.
- [x] Verify desktop and compact layouts, navigation and existing tests.
- [x] Publish this frontend-only update to the existing repository through a separate pull request: https://github.com/fredoc20231-cmyk/MBSI-Studio/pull/10.
- [x] Replace the crash-prone spot-size slider with an accessible native control; verify all pages, keyboard updates and reloads, then update the pull request.

## Multi-sample comparison

- [x] Map the backend’s observed sample, workflow and result contracts to comparison levels.
- [x] Build multi-sample selection and synchronized comparison for expression, clusters, domains, phenotypes and spatial statistics.
- [x] Wire real per-sample workflow runs and aligned returned results without fabricating scientific outputs.
- [x] Add behavior tests and verify desktop and compact workflows, including unavailable-level safeguards.
- [ ] Enable niche, cell-interaction and trajectory comparisons: blocked on the scientific API exposing those dataset workflows; the interface currently marks them unavailable.
- [x] Update the existing frontend pull request with the multi-sample comparison workspace.

## Branding

- [x] Replace the default favicon with the existing MBSI aperture mark and update the pull request.

## Repository integration

- [x] Inspect the repository's current API and deployment setup and wire every API request to a checked scientific service address.
- [x] Test the connection/upload contract and unavailable-service UI on desktop and compact screens; live uploads remain blocked on the deployed HTTPS API address.
- [x] Publish frontend-only connection changes through a separate pull request stacked on #10: https://github.com/fredoc20231-cmyk/MBSI-Studio/pull/11.
- [x] Verify access to the existing MBSI-Studio repository and inspect its backend.
- [x] Add the current frontend under frontend/ through a separate pull request: https://github.com/fredoc20231-cmyk/MBSI-Studio/pull/9 (open for review and merge).
- [x] Verify frontend tests, all seven page openings, and that every original repository entry remains unchanged.
- [x] Add Samples page: multi-file upload, guided FASTQ → CytAssist → slide steps, groups and assignment.
- [ ] Connect to the deployed backend: blocked on its HTTPS API address and allowed frontend origins.
- Automatic two-way Git sync with this existing repository is not supported; repository updates use explicit GitHub API operations.

## Visium capability roadmap

- [x] Backend PR #12 closed; Visium analyses await the backend team (PR #8).
- [x] Visium page showing live backend capabilities and running each module.
- [ ] Phase 8 benchmarking on public 10x data: blocked on a running backend with the new libraries installed.

## Additional audit (frontend only; no scientific Python changes from Lovable)

- [x] Closed backend PR #12 (frontend-only rule).
- [ ] Dataset metadata (project, sample, platform, tissue, library ID, replicate), readiness and QC warnings.
- [ ] Real tissue-coordinate viewer with gene search, overlays, legends, zoom: blocked on backend returning coordinates/expression.
- [ ] Spatial statistics, domains, deconvolution, DE, CCI, provenance and report views driven by backend artifacts.
- [ ] Browser tests against the deployed backend, new PR to main, merge and domain check: blocked on the deployed HTTPS API address.
