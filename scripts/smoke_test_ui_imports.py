#!/usr/bin/env python3
"""Smoke test UI component imports."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    from app.components.topnav import render_topnav, NAV_PAGES, resolve_page_path
    from app.components.statusbar import render_statusbar
    from app.components.layout import inject_styles, render_analysis_subtabs
    from app.components.analysis_panels import (
        render_spatial_map_panel,
        render_cell_types_panel,
        render_clusters_panel,
        render_neighborhoods_panel,
        render_boundaries_panel,
        render_pathways_panel,
        render_3d_panel,
    )
    from app.components.safe import safe_get, safe_dataframe, safe_plotly

    assert callable(render_topnav)
    assert callable(render_statusbar)
    assert callable(render_analysis_subtabs)
    assert len(NAV_PAGES) == 14
    assert resolve_page_path("streamlit_app.py") == "streamlit_app.py"
    assert resolve_page_path("pages/missing.py") is None

    for fn in (
        render_spatial_map_panel,
        render_cell_types_panel,
        render_clusters_panel,
        render_neighborhoods_panel,
        render_boundaries_panel,
        render_pathways_panel,
        render_3d_panel,
    ):
        assert callable(fn)

    assert safe_get({"a": {"b": 1}}, "a", "b") == 1
    assert safe_get({}, "x", default=0) == 0

    print("UI imports smoke test PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
