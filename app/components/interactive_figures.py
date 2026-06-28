"""Interactive Plotly figures with report registration and docking."""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from app.components.safe import safe_plotly
from app.components.theme import apply_plotly_theme

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "scrollZoom": True,
    "modeBarButtonsToAdd": ["drawclosedpath", "eraseshape"],
    "toImageButtonOptions": {"format": "png", "filename": "mbsi_figure", "scale": 2},
}


def render_interactive_plot(
    fig: Any,
    title: str = "",
    module: str = "",
    register: bool = True,
    key: Optional[str] = None,
    dockable: bool = True,
) -> bool:
    """Render Plotly figure with full toolbar; optionally register for report."""
    if fig is None:
        st.info("Plot unavailable.")
        return False
    plot_key = key or f"plot_{module}_{title}".replace(" ", "_").lower()[:40]
    if dockable:
        return render_dockable_plot(fig, key=plot_key, title=title, module=module, register=register)
    return _render_plotly(fig, title=title, module=module, register=register, key=plot_key)


def render_dockable_plot(
    fig: Any,
    key: str,
    title: Optional[str] = None,
    module: str = "",
    register: bool = True,
) -> bool:
    """Inline plot plus pop-out expander with full-width duplicate."""
    if fig is None:
        st.info("Plot unavailable.")
        return False
    try:
        header = title or "Figure"
        col1, col2 = st.columns([5, 1])
        with col2:
            pop = st.button("Pop out", key=f"{key}_pop", use_container_width=True)
        with col1:
            if title:
                st.caption(header)
        ok = _render_plotly(fig, title=title or "", module=module, register=register, key=key)
        if pop:
            st.session_state[f"{key}_expanded"] = True
        if st.session_state.get(f"{key}_expanded"):
            with st.expander(f"🔍 {header} — full view", expanded=True):
                _render_plotly(fig, title=title or "", module=module, register=False, key=f"{key}_full")
                if st.button("Close", key=f"{key}_close"):
                    st.session_state[f"{key}_expanded"] = False
                    st.rerun()
        return ok
    except Exception as exc:
        return safe_plotly(fig, message=f"Plot error: {exc}")


def _render_plotly(
    fig: Any,
    title: str = "",
    module: str = "",
    register: bool = True,
    key: Optional[str] = None,
) -> bool:
    try:
        if title and hasattr(fig, "update_layout"):
            fig.update_layout(title=title)
        apply_plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key=key)
        if register and module:
            try:
                from mbsi.reports.registry import register_figure
                register_figure(module, title or "figure", fig)
            except Exception:
                pass
        return True
    except Exception as exc:
        return safe_plotly(fig, message=f"Plot error: {exc}")
