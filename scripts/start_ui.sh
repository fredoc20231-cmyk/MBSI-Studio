#!/usr/bin/env bash
# Start MBSI Studio Streamlit UI on http://127.0.0.1:8501
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-/Users/afadiel01/miniforge3/bin/python3}"
PORT="${PORT:-8501}"
HOST="${HOST:-127.0.0.1}"

cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

# Free the port if a stale Streamlit process is still bound
if command -v lsof >/dev/null 2>&1; then
  OLD_PIDS="$(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$OLD_PIDS" ]]; then
    echo "Stopping existing listener(s) on port $PORT: $OLD_PIDS"
    kill $OLD_PIDS 2>/dev/null || true
    sleep 1
  fi
fi

echo "Starting MBSI Studio at http://${HOST}:${PORT}"
exec "$PYTHON" -m streamlit run app/streamlit_app.py \
  --server.address="$HOST" \
  --server.port="$PORT" \
  --server.headless=true
