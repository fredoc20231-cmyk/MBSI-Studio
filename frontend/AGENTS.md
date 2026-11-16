# Frontend architecture

- Keep this directory as the standalone TanStack web frontend; leave the sibling scientific backend unchanged. Why: isolate frontend deployment from scientific computation.
- Route all scientific calls through src/lib/mbsi-api.ts and the configured VITE_MBSI_API_URL. Why: the existing FastAPI application is the sole analysis source.
- Show unavailable or empty states until observed API results arrive. Why: preserve biomedical data integrity.
- Keep pinned TanStack versions and regenerate src/routeTree.gen.ts through the routing plugin. Why: preserve target compatibility without committing generated code.
