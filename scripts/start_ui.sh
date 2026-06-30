#!/usr/bin/env bash
# Start MBSI Studio Streamlit UI on http://127.0.0.1:8501
# SAFE=1 uses app/safe_streamlit_app.py for import-error isolation
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-/Users/afadiel01/miniforge3/bin/python3}"
PORT="${PORT:-8501}"
HOST="${HOST:-127.0.0.1}"
HEADLESS="${HEADLESS:-false}"
SAFE="${SAFE:-${MBSI_SAFE_UI:-0}}"
APP="${APP:-app/streamlit_app.py}"
if [[ "$SAFE" == "1" || "$SAFE" == "true" ]]; then
  APP="app/safe_streamlit_app.py"
fi

cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

# Stop stale Streamlit processes (common cause of blank/broken UI)
pkill -f "streamlit run app/streamlit_app.py" 2>/dev/null || true
pkill -f "streamlit run app/safe_streamlit_app.py" 2>/dev/null || true
sleep 1

# Free the port if still bound
if command -v lsof >/dev/null 2>&1; then
  OLD_PIDS="$(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$OLD_PIDS" ]]; then
    echo "Stopping existing listener(s) on port $PORT: $OLD_PIDS"
    kill $OLD_PIDS 2>/dev/null || true
    sleep 1
    STILL="$(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$STILL" ]]; then
      kill -9 $STILL 2>/dev/null || true
      sleep 1
    fi
  fi
fi

URL="http://${HOST}:${PORT}"
echo "============================================"
echo "  MBSI Studio UI"
echo "  Open in browser: ${URL}"
echo "  Entry: ${APP}"
echo "============================================"

exec "$PYTHON" -m streamlit run "$APP" \
  --server.address="$HOST" \
  --server.port="$PORT" \
  --server.headless="$HEADLESS" \
  --browser.gatherUsageStats=false
