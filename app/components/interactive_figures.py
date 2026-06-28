"""Interactive Plotly figures with report registration."""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from app.components.safe import safe_plotly

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "scrollZoom": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "png", "filename": "mbsi_figure", "scale": 2},
}


def render_interactive_plot(
    fig: Any,
    title: str = "",
    module: str = "",
    register: bool = True,
    key: Optional[str] = None,
) -> bool:
    """Render Plotly figure with full toolbar; optionally register for report."""
    if fig is None:
        st.info("Plot unavailable.")
        return False
    try:
        if title and hasattr(fig, "update_layout"):
            fig.update_layout(title=title)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key=key)
        if register and module:
            from mbsi.reports.registry import register_figure
            register_figure(module, title or "figure", fig)
        return True
    except Exception as exc:
        return safe_plotly(fig, message=f"Plot error: {exc}")
