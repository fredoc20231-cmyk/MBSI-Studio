"""TME marker gene sets for program scoring."""

TME_MARKER_SETS = {
    "immune_exclusion": {
        "tumor": ["EPCAM", "KRT8", "MKI67"],
        "immune": ["CD8A", "CD3D", "MS4A1"],
        "label": "Immune Exclusion",
    },
    "caf_barrier": {
        "caf": ["ACTA2", "FAP", "COL1A1"],
        "tumor": ["EPCAM", "KRT8"],
        "label": "CAF Barrier",
    },
    "tls_like": {
        "tls": ["MS4A1", "BCL6", "CXCL13", "CD3D"],
        "label": "TLS-like Niche",
    },
    "hypoxia": {
        "hypoxia": ["HIF1A", "CA9", "SLC2A1"],
        "label": "Hypoxic Niche",
    },
    "angiogenesis": {
        "angiogenesis": ["VEGFA", "KDR", "PECAM1"],
        "label": "Angiogenic Region",
    },
    "invasion": {
        "tumor": ["EPCAM", "MKI67"],
        "stromal": ["ACTA2", "COL1A1"],
        "label": "Invasive Front",
    },
}
