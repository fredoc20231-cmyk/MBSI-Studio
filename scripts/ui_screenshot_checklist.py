#!/usr/bin/env python3
"""Manual screenshot QA checklist for the reference dashboard cockpit."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CHECKLIST = [
    "Top navbar: single row — brand, nav buttons, Demo Mode / Help / Settings / AU",
    "No duplicate Streamlit page_link navigation row under header",
    "Analysis subtabs visible and clickable (Spatial Map active by default)",
    "Left sidebar: project summary, modalities, analysis status, readiness ring",
    "Histology card: H&E image, cell dots, irregular boundary contours, 250 µm scale bar",
    "Map toolbar visible above histology panel",
    "Metric strip: 5 cards (cells, types, resolution, boundary leakage, Moran's I)",
    "Right panels: neighborhood graph, interactions bar, pathway table, ligand gradient",
    "Bottom row: 6 analytics cards (marker, composition, trajectory, causal, invasion, twin)",
    "Status bar fixed at bottom with system indicators",
    "Export All writes files under data/outputs/",
]


def main() -> None:
    print("MBSI Studio — Dashboard Screenshot Checklist")
    print("Launch: MBSI_DASHBOARD=1 streamlit run app/streamlit_app.py")
    print("-" * 60)
    for idx, item in enumerate(CHECKLIST, start=1):
        print(f"[ ] {idx:02d}. {item}")
    print("-" * 60)
    print(f"{len(CHECKLIST)} visual checks listed.")


if __name__ == "__main__":
    main()
