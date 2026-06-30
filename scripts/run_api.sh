#!/usr/bin/env bash
# Start MBSI Studio Builder.io-facing API on http://127.0.0.1:8000
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-/Users/afadiel01/miniforge3/bin/python3}"
PORT="${PORT:-8000}"
HOST="${HOST:-127.0.0.1}"

cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "============================================"
echo "  MBSI Studio API"
echo "  Open: http://${HOST}:${PORT}/docs"
echo "============================================"

exec "$PYTHON" -m uvicorn mbsi.api.app:app \
  --host "$HOST" \
  --port "$PORT" \
  --reload
