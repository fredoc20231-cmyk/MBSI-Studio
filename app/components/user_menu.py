"""Minimal user menu for local-mode MBSI Studio."""

from __future__ import annotations

import streamlit as st

from app.components.settings_panel import APP_VERSION, _git_commit_sha


@st.dialog("Account", width="small")
def _user_menu_dialog() -> None:
    st.markdown("#### Local profile")
    st.markdown("**User:** Research Operator (local)")
    st.caption("Local mode — no authentication configured.")

    st.divider()
    st.markdown(f"**MBSI Studio** v{APP_VERSION}")
    st.caption(f"Commit `{_git_commit_sha()}` — use header **Settings** for preferences.")

    st.divider()
    if st.button("Sign out", key="user_menu_sign_out", use_container_width=True):
        st.info("Local mode — no auth. Session remains active on this machine.")


def render_user_menu() -> None:
    """Header user menu control."""
    if st.button("User", key="header_user_btn", help="Account menu"):
        _user_menu_dialog()
