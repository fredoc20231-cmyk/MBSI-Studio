# API container for Render; scientific GPU workers should use a separate image.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml README.md ./
# PyPI's default torch wheel may pull in a large CUDA stack on Linux.
# This service runs CPU workloads; keep GPU training in dedicated workers.
RUN python -m pip install --upgrade pip \
    && python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.5.1+cpu"

COPY . .
RUN python -m pip install -r requirements.txt \
    && python -m pip install --no-deps .

RUN mkdir -p /app/data/uploads /app/data/outputs /app/data/registry/ingested

# Render injects PORT. Do not hardcode 8000: a live container must listen
# on the port that Render routes external traffic to.
EXPOSE 10000
CMD ["sh", "-c", "exec python -m uvicorn mbsi.api.app:app --host 0.0.0.0 --port ${PORT:-10000}"]
