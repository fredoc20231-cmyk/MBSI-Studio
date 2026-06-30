#!/usr/bin/env python3
"""Comprehensive launch import smoke test — streamlit app, workspaces, mbsi packages."""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

WORKSPACE_MODULES = [
    "app.workspaces.study_data",
    "app.workspaces.qc_transformation",
    "app.workspaces.visualization",
    "app.workspaces.spatial_variable_genes",
    "app.workspaces.spatial_gene_sets",
    "app.workspaces.spatial_domains",
    "app.workspaces.phenotyping",
    "app.workspaces.differential_analysis",
    "app.workspaces.spatial_gradients",
    "app.workspaces.segment_register",
    "app.workspaces.reconstruction",
    "app.workspaces.benchmark",
    "app.workspaces.discovery",
    "app.workspaces.ai_review",
    "app.workspaces.report_export",
    "app.workspaces.settings",
]

OPTIONAL_DEPS = ("cellpose", "gseapy", "squidpy", "tangram", "scvi")


def _discover_mbsi_top_level() -> list[str]:
    import mbsi

    names = []
    pkg_path = Path(mbsi.__file__).parent
    for mod in pkgutil.iter_modules([str(pkg_path)]):
        if mod.ispkg:
            names.append(f"mbsi.{mod.name}")
    return sorted(names)


def _try_import(name: str) -> str | None:
    try:
        importlib.import_module(name)
        return None
    except Exception as exc:
        return f"{name}: {exc}"


def main() -> int:
    failures: list[str] = []

    for name in ("app.streamlit_app", "app.safe_streamlit_app", "app.components.saas_shell"):
        err = _try_import(name)
        if err:
            failures.append(err)

    for name in WORKSPACE_MODULES:
        err = _try_import(name)
        if err:
            failures.append(err)

    for name in _discover_mbsi_top_level():
        err = _try_import(name)
        if err:
            failures.append(err)

    for name in ("mbsi.api.app", "mbsi.io.ingest_universal", "mbsi.schema.serialize"):
        err = _try_import(name)
        if err:
            failures.append(err)

    optional_notes: list[str] = []
    for name in OPTIONAL_DEPS:
        err = _try_import(name)
        if err:
            optional_notes.append(err)

    if failures:
        print("LAUNCH IMPORT SMOKE TEST FAILED")
        for f in failures:
            print(f"  FAIL {f}")
        if optional_notes:
            print("\nOptional dependency notes (non-fatal):")
            for n in optional_notes:
                print(f"  NOTE {n}")
        return 1

    print("Launch import smoke test PASSED")
    print(f"  streamlit entry + {len(WORKSPACE_MODULES)} workspaces + {len(_discover_mbsi_top_level())} mbsi packages")
    if optional_notes:
        print("Optional deps not installed (OK):")
        for n in optional_notes:
            print(f"  NOTE {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
