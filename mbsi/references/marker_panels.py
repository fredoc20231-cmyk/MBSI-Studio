"""Built-in marker panels and manual upload parsing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

BUILTIN_PANELS: Dict[str, List[str]] = {
    "immune": ["CD3D", "CD8A", "CD4", "CD68", "FOXP3", "NCAM1", "MS4A1"],
    "stromal": ["COL1A1", "ACTA2", "FAP", "PDGFRA", "DCN", "LUM"],
    "epithelial": ["EPCAM", "KRT8", "KRT18", "KRT19", "MUC1", "CDH1"],
    "endothelial": ["PECAM1", "VWF", "CDH5", "ENG", "KDR"],
    "myeloid": ["CD14", "CD163", "ITGAM", "CSF1R", "LYZ"],
    "t_cell": ["CD3D", "CD3E", "CD8A", "CD4", "TRAC"],
    "b_cell": ["MS4A1", "CD79A", "CD19", "CD37"],
}


def list_panels() -> List[str]:
    return list(BUILTIN_PANELS.keys())


def get_panel(name: str) -> List[str]:
    return list(BUILTIN_PANELS.get(name.lower(), BUILTIN_PANELS["immune"]))


def parse_panel_upload(content: str) -> List[str]:
    """Parse manual panel upload (comma or newline separated genes)."""
    genes = []
    for line in content.replace(",", "\n").splitlines():
        g = line.strip()
        if g and not g.startswith("#"):
            genes.append(g)
    return genes


def panel_dataframe(name: str) -> pd.DataFrame:
    genes = get_panel(name)
    return pd.DataFrame({"gene": genes, "panel": name})
