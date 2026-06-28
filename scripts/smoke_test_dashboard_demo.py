#!/usr/bin/env python3
"""Smoke test dashboard demo generation and analysis panels."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from app.components.demo_data import generate_dashboard_demo
    from app.components.analysis_panels import (
        render_spatial_map_panel,
        render_cell_types_panel,
        render_clusters_panel,
    )
    from app.components.layout import render_analysis_subtabs

    demo = generate_dashboard_demo(seed=42)
    assert "histology_image" in demo
    assert "cells" in demo
    assert "summary" in demo
    assert demo["summary"]["spots"] > 0

    assert callable(render_analysis_subtabs)
    assert callable(render_spatial_map_panel)
    assert callable(render_cell_types_panel)
    assert callable(render_clusters_panel)

    print(f"Dashboard demo OK: {demo['summary']['spots']} spots, {len(demo['cells'])} cells")
    print("Dashboard demo smoke test PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
