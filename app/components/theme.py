"""Day/night theme for MBSI SaaS shell."""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st
import streamlit.components.v1 as components

THEME_KEY = "mbsi_theme"
VALID_THEMES = ("dark", "light")

THEME_PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#07111f",
        "panel": "#0d1828",
        "panel2": "#101d2e",
        "border": "#22314a",
        "text": "#f4f7fb",
        "muted": "#9aa7b8",
        "blue": "#4f7cff",
        "green": "#39d98a",
        "orange": "#ffb020",
        "red": "#ff5c7a",
        "purple": "#9b6cff",
        "cyan": "#30d5c8",
        "pink": "#ff5c9c",
        "plot_paper": "#0d1828",
        "plot_bg": "#101d2e",
        "plot_font": "#f4f7fb",
        "plot_grid": "#22314a",
    },
    "light": {
        "bg": "#f4f7fb",
        "panel": "#ffffff",
        "panel2": "#eef2f8",
        "border": "#c8d4e3",
        "text": "#1a2332",
        "muted": "#5a6b7d",
        "blue": "#2563eb",
        "green": "#059669",
        "orange": "#d97706",
        "red": "#dc2626",
        "purple": "#7c3aed",
        "cyan": "#0891b2",
        "pink": "#db2777",
        "plot_paper": "#ffffff",
        "plot_bg": "#f8fafc",
        "plot_font": "#1a2332",
        "plot_grid": "#e2e8f0",
    },
}


def init_theme_state() -> None:
    """Initialize theme from session, query params, or default dark."""
    qp = getattr(st, "query_params", None)
    if qp is not None and "theme" in qp:
        raw = str(qp.get("theme", "")).lower()
        if raw in VALID_THEMES:
            st.session_state[THEME_KEY] = raw
    st.session_state.setdefault(THEME_KEY, "dark")


def get_theme() -> str:
    theme = st.session_state.get(THEME_KEY, "dark")
    return theme if theme in VALID_THEMES else "dark"


def set_theme(theme: str) -> None:
    if theme not in VALID_THEMES:
        return
    st.session_state[THEME_KEY] = theme
    qp = getattr(st, "query_params", None)
    if qp is not None:
        try:
            qp["theme"] = theme
        except Exception:
            pass


def get_plotly_theme_colors() -> Dict[str, str]:
    return dict(THEME_PALETTES[get_theme()])


def apply_plotly_theme(fig: Any) -> Any:
    """Apply paper/bg/font colors from active session theme."""
    if fig is None or not hasattr(fig, "update_layout"):
        return fig
    c = get_plotly_theme_colors()
    layout_kwargs: Dict[str, Any] = {
        "paper_bgcolor": c["plot_paper"],
        "plot_bgcolor": c["plot_bg"],
        "font": dict(color=c["plot_font"]),
        "xaxis": dict(gridcolor=c["plot_grid"], zerolinecolor=c["plot_grid"], color=c["plot_font"]),
        "yaxis": dict(gridcolor=c["plot_grid"], zerolinecolor=c["plot_grid"], color=c["plot_font"]),
    }
    if get_theme() == "light":
        layout_kwargs["title"] = dict(font=dict(color=c["plot_font"]))
        layout_kwargs["legend"] = dict(font=dict(color=c["plot_font"]))
    fig.update_layout(**layout_kwargs)
    return fig


def _css_vars_block(selector: str, palette: Dict[str, str]) -> str:
    lines = [f"{selector} {{"]
    for key, val in palette.items():
        if key.startswith("plot_"):
            continue
        lines.append(f"  --{key}: {val};")
    lines.append("}")
    return "\n".join(lines)


def _light_mode_widget_css() -> str:
    """Explicit Streamlit widget overrides — fixes white-on-white in day mode."""
    return """
.stApp[data-mbsi-theme="light"],
[data-mbsi-theme="light"] .stApp {
  background: var(--bg) !important;
  color: var(--text) !important;
}
.stApp[data-mbsi-theme="light"] p,
.stApp[data-mbsi-theme="light"] span,
.stApp[data-mbsi-theme="light"] label,
.stApp[data-mbsi-theme="light"] li,
.stApp[data-mbsi-theme="light"] h1,
.stApp[data-mbsi-theme="light"] h2,
.stApp[data-mbsi-theme="light"] h3,
.stApp[data-mbsi-theme="light"] h4,
.stApp[data-mbsi-theme="light"] h5,
.stApp[data-mbsi-theme="light"] h6,
.stApp[data-mbsi-theme="light"] div[data-testid="stMarkdownContainer"] p,
.stApp[data-mbsi-theme="light"] div[data-testid="stMarkdownContainer"] li,
.stApp[data-mbsi-theme="light"] div[data-testid="stCaptionContainer"],
.stApp[data-mbsi-theme="light"] div[data-testid="stCaptionContainer"] p,
.stApp[data-mbsi-theme="light"] div[data-testid="stMetricValue"],
.stApp[data-mbsi-theme="light"] div[data-testid="stMetricLabel"] {
  color: var(--text) !important;
}
.stApp[data-mbsi-theme="light"] div[data-testid="stMetricLabel"],
.stApp[data-mbsi-theme="light"] small,
.stApp[data-mbsi-theme="light"] .stCaption {
  color: var(--muted) !important;
}
.stApp[data-mbsi-theme="light"] .stButton > button {
  color: var(--text) !important;
  background-color: var(--panel2) !important;
  border: 1px solid var(--border) !important;
}
.stApp[data-mbsi-theme="light"] .stButton > button[kind="primary"],
.stApp[data-mbsi-theme="light"] .stButton > button[data-testid="baseButton-primary"] {
  color: #ffffff !important;
  background-color: var(--blue) !important;
  border-color: var(--blue) !important;
}
.stApp[data-mbsi-theme="light"] div[data-baseweb="select"] > div,
.stApp[data-mbsi-theme="light"] div[data-baseweb="input"] > div,
.stApp[data-mbsi-theme="light"] input,
.stApp[data-mbsi-theme="light"] textarea {
  background-color: var(--panel) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
}
.stApp[data-mbsi-theme="light"] div[data-baseweb="select"] span,
.stApp[data-mbsi-theme="light"] div[data-baseweb="input"] input {
  color: var(--text) !important;
}
.stApp[data-mbsi-theme="light"] [data-testid="stDataFrame"],
.stApp[data-mbsi-theme="light"] [data-testid="stTable"] {
  color: var(--text) !important;
}
.stApp[data-mbsi-theme="light"] [data-testid="stChatMessage"],
.stApp[data-mbsi-theme="light"] [data-testid="stChatMessageContent"] {
  color: var(--text) !important;
  background: var(--panel2) !important;
}
.stApp[data-mbsi-theme="light"] .saas-left-nav,
.stApp[data-mbsi-theme="light"] .saas-top-bar,
.stApp[data-mbsi-theme="light"] .saas-workspace,
.stApp[data-mbsi-theme="light"] .saas-drawer {
  color: var(--text) !important;
}
.stApp[data-mbsi-theme="light"] .saas-context-module {
  color: var(--text) !important;
}
.stApp[data-mbsi-theme="light"] div[data-testid="stRadio"] label,
.stApp[data-mbsi-theme="light"] div[data-testid="stCheckbox"] label,
.stApp[data-mbsi-theme="light"] div[data-testid="stSelectbox"] label,
.stApp[data-mbsi-theme="light"] div[data-testid="stSlider"] label {
  color: var(--text) !important;
}
.stApp[data-mbsi-theme="light"] [data-testid="stAlert"],
.stApp[data-mbsi-theme="light"] [data-baseweb="notification"] {
  color: var(--text) !important;
}
"""


def inject_theme_styles() -> None:
    """Inject theme CSS variables onto .stApp and set data-mbsi-theme on document."""
    theme = get_theme()
    palette = THEME_PALETTES[theme]
    ui_palette = {k: v for k, v in palette.items() if not k.startswith("plot_")}

    css_parts = [
        _css_vars_block(".stApp", ui_palette),
        _css_vars_block(".saas-app", ui_palette),
        _css_vars_block(".mbsi-app", ui_palette),
        f'.stApp {{ color: {ui_palette["text"]} !important; background: {ui_palette["bg"]} !important; }}',
    ]
    if theme == "light":
        css_parts.append(_light_mode_widget_css())

    st.markdown(f"<style>\n{chr(10).join(css_parts)}\n</style>", unsafe_allow_html=True)
    components.html(
        f"""
        <script>
        (function() {{
          var t = "{theme}";
          function apply(doc) {{
            if (!doc) return;
            doc.documentElement.setAttribute("data-mbsi-theme", t);
            var app = doc.querySelector(".stApp");
            if (app) app.setAttribute("data-mbsi-theme", t);
          }}
          try {{ apply(window.parent.document); }} catch (e) {{}}
          try {{ apply(document); }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_theme_quick_toggle(compact: bool = False) -> None:
    """Sun/moon quick toggle for top bar or nav footer."""
    theme = get_theme()
    if compact:
        icon = "☀️" if theme == "dark" else "🌙"
        label = "Day mode" if theme == "dark" else "Night mode"
        if st.button(f"{icon} {label}", key="theme_quick_toggle", use_container_width=True):
            set_theme("light" if theme == "dark" else "dark")
            st.rerun()
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("☀️ Day", key="theme_day_btn", type="primary" if theme == "light" else "secondary"):
                set_theme("light")
                st.rerun()
        with c2:
            if st.button("🌙 Night", key="theme_night_btn", type="primary" if theme == "dark" else "secondary"):
                set_theme("dark")
                st.rerun()


def render_theme_settings() -> None:
    """Full theme picker for Settings workspace."""
    theme = get_theme()
    st.markdown("#### Appearance")
    choice = st.radio(
        "Color theme",
        options=["dark", "light"],
        format_func=lambda x: "🌙 Night — dark background (default)" if x == "dark" else "☀️ Day — light background",
        index=0 if theme == "dark" else 1,
        key="settings_theme_radio",
        horizontal=True,
    )
    if choice != theme:
        set_theme(choice)
        st.rerun()
    if theme == "light":
        st.caption("Day mode uses light panels and dark text for bright environments.")
    else:
        st.caption("Night mode uses dark panels and light text for low-glare viewing.")
