# MBSI Studio Render + Lovable recovery

Existing Render service ID: `srv-dbshsbjbc2fs73bk3d30`.
Existing API URL: `https://mbsi-studio.onrender.com`.
Lovable site: `https://mbsi-studio.cronus.life`.
GitHub: `fredoc20231-cmyk/MBSI-Studio`, branch `main`.

## Why the current deployment cannot serve the frontend

The deployment reported as **Live** was built from `60a254ab948d6405e29ea3c1cff3289b18710395`, predating the merged API endpoints (main at `9967c12e...` before this fix).
A Render "Live" badge reports its own deploy state; it does not prove the latest GitHub main has deployed or that the public HTTP endpoint works.

Fixes in this repository:
- Docker binds `0.0.0.0:${PORT:-10000}`; avoids hardcoded `8000` and defaults to Render's expected port.
- Startup script also reads `PORT`, does not force `127.0.0.1`, and disables development reload by default.
- Docker installs CPU-only PyTorch before requirements, avoiding multi-GB CUDA dependencies on a CPU API service.
- Root `/` now returns a service descriptor; `/api/health`, `/openapi.json` are health/contract probes.
- CORS permits the exact production Lovable origin even without configuration; set `MBSI_CORS_ORIGINS` explicitly for production and permitted preview domains.
- Production React API client uses Render instead of the **visitor's localhost**, and `/api/v1/datasets` is now queried rather than stubbed.

## One-time Render dashboard actions

Go to https://dashboard.render.com/web/srv-dbshsbjbc2fs73bk3d30.

1. **Settings → Build & Deploy**: repository `fredoc20231-cmyk/MBSI-Studio`; branch `main`. Confirm the service deploys on main updates; enable automatic deployment after CI if available. An existing service is **not automatically reconfigured** by simply committing `render.yaml`.
2. Runtime should be **Docker** using `./Dockerfile` and root directory `.`. If configured for Python-native runtime instead: start command `bash scripts/run_api.sh` and ensure all dependencies are installed. Prefer Docker for consistency.
3. **Environment**: `MBSI_CORS_ORIGINS=https://mbsi-studio.cronus.life` (comma-add approved preview origins only), `PYTHONUNBUFFERED=1`, and `PYTHONPATH=/app` for Docker. `PORT` normally is supplied by Render; do not force the app to listen on a different port.
4. **Health Check Path**: `/api/health`. If a persistent disk exists, mount `/app/data`. Without durable disk, uploads, projects, and run history will not persist across redeploys.
5. **Manual Deploy → Deploy latest commit**, then inspect **Events** and **Logs** until deployment succeeds. Verify that the deployed commit SHA is the latest `main`, **not `60a254a`**.
6. Browser probes:
   - `https://mbsi-studio.onrender.com/` should respond with a service JSON descriptor;
   - `https://mbsi-studio.onrender.com/api/health` should respond with `{"status":"healthy",...}`;
   - `https://mbsi-studio.onrender.com/openapi.json` should respond with FastAPI OpenAPI JSON;
   - `https://mbsi-studio.onrender.com/api/v1/datasets` should respond with `{"datasets":[]}` (until uploaded).
7. From the Lovable site, verify the **Network** panel points requests to the Render HTTPS hostname, not to `localhost:8000`. Use `VITE_MBSI_API_URL=https://mbsi-studio.onrender.com` in Lovable's build environment and republish. Vite environment values are injected at **build time**.

If a deploy fails, copy the first Python exception in Render logs or the exact build error. The GitHub CI smoke test is **not** a substitute for Render deployment verification.

## Browser connectivity smoke test

From a browser console on the Lovable origin, run:

```js
fetch("https://mbsi-studio.onrender.com/api/health")
  .then(async r => ({status: r.status, payload: await r.json()}))
  .then(console.log).catch(console.error);
```

A successful CORS fetch proves basic browser connectivity only, not authentication, workload readiness, or scientific validity.

**Safety**: This public API currently lacks production tenant authentication, secure storage, and quotas. Do not upload patient-identifiable data or expose the service as clinical production until those controls are implemented and reviewed.
