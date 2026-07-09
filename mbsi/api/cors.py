"""CORS configuration — env-driven allowed origins (no wildcard by default)."""

from __future__ import annotations

import os


def cors_allow_origins() -> list[str]:
    """
    Read allowed origins from MBSI_CORS_ORIGINS (comma-separated).

    Defaults to local Streamlit origins. Set to ``*`` only for explicit dev override.
    """
    raw = os.environ.get(
        "MBSI_CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000",
    )
    if raw.strip() == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
