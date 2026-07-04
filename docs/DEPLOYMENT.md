# Deployment Guide

## Environments

| Profile     | File                       | Server mode                     |
| ----------- | -------------------------- | ------------------------------- |
| Development | `docker-compose.yml`       | uvicorn `--reload`, bind mount  |
| Production  | `docker-compose.prod.yml`  | uvicorn `--workers`, healthchecks |

## Production deployment (Docker Compose)

1. **Configure environment**
   ```bash
   cp .env.example .env
   # edit .env: set MBSI_CORS_ALLOW_ORIGINS to your frontend origin(s),
   # WEB_CONCURRENCY to your CPU budget, etc.
   ```

2. **Build and start**
   ```bash
   docker compose -f docker-compose.prod.yml up --build -d
   ```

3. **Verify health**
   ```bash
   curl http://localhost:8000/readyz     # {"status":"ready",...}
   curl http://localhost:8000/health     # {"status":"healthy",...}
   ```

## Health & readiness probes

| Endpoint   | Purpose                          | Kubernetes mapping |
| ---------- | -------------------------------- | ------------------ |
| `/health`  | Liveness (process is up)         | livenessProbe      |
| `/healthz` | Liveness alias (k8s convention)  | livenessProbe      |
| `/readyz`  | Readiness (can serve requests)   | readinessProbe     |

## Reproducible dependencies

- `requirements.txt` — human-maintained direct deps (loose ranges).
- `requirements.lock.txt` — pinned versions for reproducible builds.

Regenerate the lock with pip-tools:
```bash
pip install pip-tools
pip-compile requirements.txt -o requirements.lock.txt
```

## CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`:
- **lint** — black (format check), flake8, mypy (non-blocking)
- **test** — pytest matrix on Python 3.10/3.11/3.12 with coverage (fails under 60%)
- **build-image** — `docker build` sanity check
- **security-scan** — `pip-audit` dependency vulnerability scan

## Kubernetes (reference)

Map the probes and set resource limits. Example probe stanza:
```yaml
livenessProbe:
  httpGet: { path: /healthz, port: 8000 }
  initialDelaySeconds: 40
  periodSeconds: 30
readinessProbe:
  httpGet: { path: /readyz, port: 8000 }
  initialDelaySeconds: 10
  periodSeconds: 10
```

## Security notes

See [SECURITY.md](../SECURITY.md). Key points:
- Set an explicit CORS allowlist (`MBSI_CORS_ALLOW_ORIGINS`) — never `*` in production.
- Never expose the development profile (`--reload`) to untrusted networks.
- Run with least-privilege filesystem access to `data/`.
