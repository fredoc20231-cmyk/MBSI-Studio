"""Production vs developer mode — demo/simulation gated behind DEVELOPER_MODE=true."""

from __future__ import annotations

import os


def is_developer_mode() -> bool:
    """True when DEVELOPER_MODE env is set (demo, synthetic, cockpit dashboards)."""
    return os.environ.get("DEVELOPER_MODE", "").strip().lower() in ("1", "true", "yes", "on")


def production_mode_message() -> str:
    return (
        "Production mode is active. Upload real spatial data in **Study & Data** to run "
        "ingest, QC, visualization, and export. Set `DEVELOPER_MODE=true` to enable labeled demos."
    )


def block_demo_in_production(feature: str = "Demo datasets") -> bool:
    """Return True when demo feature must be blocked (production mode)."""
    return not is_developer_mode()
