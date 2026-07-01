#!/usr/bin/env python3
"""Comprehensive launch import smoke test — workspaces, mbsi packages, entrypoint syntax."""

from __future__ import annotations

import importlib
import py_compile
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

CORE_MODULES = [
    "app.components.saas_shell",
    "app.components.module_registry",
    "app.components.page_utils",
    "app.components.header_status",
    "app.components.help_panel",
    "app.components.settings_panel",
    "app.components.notification_center",
    "app.components.user_menu",
    "mbsi.api.app",
    "mbsi.io.ingest_universal",
    "mbsi.schema.serialize",
]

ENTRYPOINTS = [
    "app/streamlit_app.py",
    "app/safe_streamlit_app.py",
]

OPTIONAL_DEPS = ("cellpose", "gseapy", "squidpy", "tangram", "scvi")


def _try_import(name: str) -> str | None:
    try:
        importlib.import_module(name)
        return None
    except Exception as exc:
        return f"{name}: {exc}"


def main() -> int:
    failures: list[str] = []

    for path in ENTRYPOINTS:
        try:
            py_compile.compile(str(ROOT / path), doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"{path}: {exc}")

    for name in CORE_MODULES + WORKSPACE_MODULES:
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
    print(f"  {len(ENTRYPOINTS)} entrypoints compiled + {len(WORKSPACE_MODULES)} workspaces + {len(CORE_MODULES)} core modules")
    if optional_notes:
        print("Optional deps not installed (OK):")
        for n in optional_notes:
            print(f"  NOTE {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
