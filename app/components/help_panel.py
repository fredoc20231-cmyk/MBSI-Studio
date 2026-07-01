"""Help drawer — renders docs/USER_GUIDE.md in a dialog."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_USER_GUIDE = _REPO_ROOT / "docs" / "USER_GUIDE.md"


def _load_user_guide() -> str:
    if _USER_GUIDE.is_file():
        return _USER_GUIDE.read_text(encoding="utf-8")
    return (
        "# MBSI Studio User Guide\n\n"
        "The user guide file is missing. See project documentation in `docs/`."
    )


@st.dialog("Help & User Guide", width="large")
def _help_dialog() -> None:
    st.markdown(_load_user_guide())
    st.divider()
    st.caption("Documentation is loaded from docs/USER_GUIDE.md at runtime.")


def render_help_drawer() -> None:
    """Header Help button — opens markdown user guide."""
    if st.button("Help", key="header_help_btn", help="Open user guide"):
        _help_dialog()
