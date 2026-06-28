"""Safe UI helpers — never crash on missing data."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
import streamlit as st


def safe_get(obj: Any, *keys, default=None) -> Any:
    """Nested dict/object access without raising."""
    cur = obj
    for key in keys:
        if cur is None:
            return default
        if isinstance(cur, dict):
            if key not in cur:
                return default
            cur = cur[key]
        else:
            if not hasattr(cur, key):
                return default
            cur = getattr(cur, key)
    return cur


def safe_dataframe(df: Any, message: str = "No data available.") -> bool:
    """Render dataframe if valid; return True when shown."""
    if df is None:
        st.info(message)
        return False
    if isinstance(df, pd.DataFrame):
        if df.empty:
            st.info(message)
            return False
        st.dataframe(df, use_container_width=True, hide_index=True)
        return True
    st.info(message)
    return False


def safe_plotly(fig: Any, message: str = "Plot unavailable.", **kwargs) -> bool:
    """Render plotly figure safely."""
    if fig is None:
        st.info(message)
        return False
    try:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, **kwargs)
        return True
    except Exception as exc:
        st.warning(f"{message} ({exc})")
        return False
