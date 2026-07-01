"""Help drawer — searchable USER_GUIDE.md with keyboard shortcut reference."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

import streamlit as st

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_USER_GUIDE = _REPO_ROOT / "docs" / "USER_GUIDE.md"

KEYBOARD_SHORTCUTS: List[Tuple[str, str]] = [
    ("Ctrl/Cmd + K", "Focus module search in the header"),
    ("Ctrl/Cmd + ,", "Open Settings"),
    ("Ctrl/Cmd + Shift + N", "Open Notifications"),
    ("?", "Open Help & User Guide"),
    ("Esc", "Close open drawer or dialog"),
]


def _load_user_guide() -> str:
    if _USER_GUIDE.is_file():
        return _USER_GUIDE.read_text(encoding="utf-8")
    return (
        "# MBSI Studio User Guide\n\n"
        "The user guide file is missing. See project documentation in `docs/`."
    )


def _parse_sections(markdown: str) -> List[Tuple[str, str]]:
    """Split markdown into (heading, body) pairs by ## headings."""
    sections: List[Tuple[str, str]] = []
    pattern = re.compile(r"^## (.+)$", re.MULTILINE)
    matches = list(pattern.finditer(markdown))
    if not matches:
        return [("Overview", markdown.strip())]

    preamble = markdown[: matches[0].start()].strip()
    if preamble:
        sections.append(("Overview", preamble))

    for idx, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown)
        body = markdown[start:end].strip()
        sections.append((title, body))
    return sections


def _filter_sections(sections: List[Tuple[str, str]], query: str) -> List[Tuple[str, str]]:
    q = query.strip().lower()
    if not q:
        return sections
    return [(title, body) for title, body in sections if q in title.lower() or q in body.lower()]


@st.dialog("Help & User Guide", width="large")
def _help_dialog() -> None:
    st.markdown(
        '<div class="saas-help-drawer">',
        unsafe_allow_html=True,
    )
    guide = _load_user_guide()
    sections = _parse_sections(guide)

    query = st.text_input(
        "Search documentation",
        placeholder="Filter by heading or keyword…",
        key="help_panel_search",
    )
    filtered = _filter_sections(sections, query)

    if not filtered:
        st.info("No sections match your search.")
    else:
        for title, body in filtered:
            with st.expander(title, expanded=bool(query)):
                st.markdown(body)

    st.divider()
    st.markdown("#### Keyboard shortcuts")
    for keys, desc in KEYBOARD_SHORTCUTS:
        st.markdown(f"- **{keys}** — {desc}")
    st.caption("Loaded dynamically from docs/USER_GUIDE.md")
    st.markdown("</div>", unsafe_allow_html=True)


def render_help_drawer() -> None:
    """Header Help button — opens searchable user guide drawer."""
    if st.button("Help", key="header_help_btn", help="Open user guide ( ? )"):
        _help_dialog()
