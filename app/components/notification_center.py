"""Session-backed notification center for MBSI Studio header."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal
from uuid import uuid4

import streamlit as st

NotificationLevel = Literal["info", "success", "warning", "error"]

NOTIFICATIONS_KEY = "saas_notifications"
MAX_NOTIFICATIONS = 50


def init_notifications() -> None:
    st.session_state.setdefault(NOTIFICATIONS_KEY, [])


def push_notification(
    message: str,
    *,
    title: str = "",
    level: NotificationLevel = "info",
    source: str = "system",
    dedupe: bool = False,
) -> None:
    """Append a notification; optionally skip duplicate message+title pairs."""
    init_notifications()
    items: List[Dict[str, Any]] = st.session_state[NOTIFICATIONS_KEY]
    if dedupe:
        for item in items:
            if item.get("title") == title and item.get("message") == message:
                return
    items.insert(
        0,
        {
            "id": str(uuid4()),
            "title": title or level.title(),
            "message": message,
            "level": level,
            "source": source,
            "read": False,
            "ts": datetime.now(timezone.utc).isoformat(),
        },
    )
    st.session_state[NOTIFICATIONS_KEY] = items[:MAX_NOTIFICATIONS]


def unread_count() -> int:
    init_notifications()
    return sum(1 for n in st.session_state[NOTIFICATIONS_KEY] if not n.get("read"))


def mark_all_read() -> None:
    init_notifications()
    for n in st.session_state[NOTIFICATIONS_KEY]:
        n["read"] = True


def clear_notifications() -> None:
    st.session_state[NOTIFICATIONS_KEY] = []


def _level_icon(level: str) -> str:
    return {"success": "✅", "warning": "⚠️", "error": "❌", "info": "ℹ️"}.get(level, "ℹ️")


@st.dialog("Notifications", width="large")
def _notifications_dialog() -> None:
    init_notifications()
    mark_all_read()
    items: List[Dict[str, Any]] = st.session_state.get(NOTIFICATIONS_KEY, [])
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Mark all read", key="notif_mark_read", use_container_width=True):
            mark_all_read()
            st.rerun()
    with c2:
        if st.button("Clear all", key="notif_clear", use_container_width=True):
            clear_notifications()
            st.rerun()

    if not items:
        st.info("No notifications yet. Uploads, validations, and workflow runs appear here.")
        return

    for item in items:
        icon = _level_icon(str(item.get("level", "info")))
        read_mark = "" if item.get("read") else " • new"
        st.markdown(f"**{icon} {item.get('title', 'Notice')}{read_mark}**")
        st.caption(f"{item.get('source', 'system')} · {item.get('ts', '')[:19]}")
        st.write(item.get("message", ""))
        st.divider()


def render_notification_center() -> None:
    """Bell control + dialog opener."""
    init_notifications()
    count = unread_count()
    label = f"🔔 {count}" if count else "🔔"
    if st.button(label, key="header_notifications_btn", help="Notifications"):
        _notifications_dialog()
