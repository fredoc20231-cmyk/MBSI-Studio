#!/usr/bin/env python3
"""Verify all Streamlit nav page targets exist."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.components.topnav import NAV_PAGES, APP_DIR, resolve_page_path


def main() -> int:
    missing = []
    for label, rel in NAV_PAGES:
        if resolve_page_path(rel) is None:
            missing.append((label, rel, APP_DIR / rel))
    if missing:
        for label, rel, full in missing:
            print(f"MISSING: {label} -> {rel} ({full})")
        return 1
    print(f"OK: all {len(NAV_PAGES)} nav targets exist under {APP_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
