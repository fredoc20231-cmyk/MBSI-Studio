#!/usr/bin/env bash
# FastAPI entrypoint for local and Render deployments.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
PY="${PYTHON:-python3}"

echo "MBSI Studio API listening at http://${HOST}:${PORT}/api/health"
if [[ "${MBSI_API_RELOAD:-false}" == "true" ]]; then
    exec "$PY" -m uvicorn mbsi.api.app:app --host "$HOST" --port "$PORT" --reload
fi
exec "$PY" -m uvicorn mbsi.api.app:app --host "$HOST" --port "$PORT"
