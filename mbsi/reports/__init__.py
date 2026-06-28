"""Unified report generation."""

from mbsi.reports.biomarker_report import (
    generate_spatial_biomarker_report,
    generate_biomarker_report_text,
    BIOMARKER_DISCLAIMER,
)
from mbsi.reports.registry import register_figure, register_table, register_finding, get_registered_outputs, get_notebook_entries, clear_registry
from mbsi.reports.final_report import (
    generate_final_html_report,
    generate_final_pdf_report,
    create_data_bundle,
)

__all__ = [
    "generate_spatial_biomarker_report",
    "generate_biomarker_report_text",
    "BIOMARKER_DISCLAIMER",
    "register_figure",
    "register_table",
    "register_finding",
    "get_registered_outputs",
    "get_notebook_entries",
    "clear_registry",
    "generate_final_html_report",
    "generate_final_pdf_report",
    "create_data_bundle",
]
