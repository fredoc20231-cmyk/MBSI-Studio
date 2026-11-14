# MBSI Studio

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

## Repository integration

- [x] Verify access to the existing MBSI-Studio repository and inspect its backend.
- [x] Add the current frontend under frontend/ through a separate pull request: https://github.com/fredoc20231-cmyk/MBSI-Studio/pull/9 (open for review and merge).
- [x] Verify frontend tests, all seven page openings, and that every original repository entry remains unchanged.
- [ ] Connect to the deployed backend: blocked on its HTTPS API address and allowed frontend origins.
- Automatic two-way Git sync with this existing repository is not supported; repository updates use explicit GitHub API operations.
