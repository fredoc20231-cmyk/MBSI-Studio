"""Consistent workspace page title + subtitle pattern."""

from __future__ import annotations

import streamlit as st


def render_page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """Render a styled page header inside the workspace panel."""
    icon_html = f'<span class="mbsi-page-icon">{icon}</span>' if icon else ""
    subtitle_html = f'<p class="mbsi-page-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="mbsi-page-header">
          {icon_html}
          <div class="mbsi-page-header-text">
            <h2 class="mbsi-page-title">{title}</h2>
            {subtitle_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
