"""Day/night theme for MBSI SaaS shell."""

from __future__ import annotations

from typing import Any, Dict

import streamlit as st
import streamlit.components.v1 as components

THEME_KEY = "mbsi_theme"
VALID_THEMES = ("dark", "light")

# Professional biotech palette — deep teal accent, neutral grays
THEME_PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#0c1117",
        "panel": "#151b24",
        "panel2": "#1c2430",
        "border": "#2d3848",
        "text": "#eef2f7",
        "muted": "#8b9cb0",
        "accent": "#2dd4bf",
        "nav_bg": "#121820",
        "blue": "#6366f1",
        "green": "#34d399",
        "orange": "#fbbf24",
        "red": "#f87171",
        "purple": "#a78bfa",
        "cyan": "#22d3ee",
        "pink": "#f472b6",
        "plot_paper": "#151b24",
        "plot_bg": "#1c2430",
        "plot_font": "#eef2f7",
        "plot_grid": "#2d3848",
    },
    "light": {
        "bg": "#f8fafc",
        "panel": "#ffffff",
        "panel2": "#f1f5f9",
        "border": "#e2e8f0",
        "text": "#0f172a",
        "muted": "#64748b",
        "accent": "#0d9488",
        "nav_bg": "#f1f5f9",
        "blue": "#4f46e5",
        "green": "#059669",
        "orange": "#d97706",
        "red": "#dc2626",
        "purple": "#7c3aed",
        "cyan": "#0891b2",
        "pink": "#db2777",
        "plot_paper": "#ffffff",
        "plot_bg": "#f8fafc",
        "plot_font": "#0f172a",
        "plot_grid": "#e2e8f0",
    },
}

# Semantic aliases consumed by CSS (--mbsi-*)
_MBSI_VAR_MAP = {
    "mbsi-bg": "bg",
    "mbsi-surface": "panel",
    "mbsi-surface-alt": "panel2",
    "mbsi-text": "text",
    "mbsi-muted": "muted",
    "mbsi-accent": "accent",
    "mbsi-border": "border",
    "mbsi-nav-bg": "nav_bg",
}


def init_theme_state() -> None:
    """Initialize theme from session, query params, or default light."""
    qp = getattr(st, "query_params", None)
    if qp is not None and "theme" in qp:
        raw = str(qp.get("theme", "")).lower()
        if raw in VALID_THEMES:
            st.session_state[THEME_KEY] = raw
    st.session_state.setdefault(THEME_KEY, "light")


def get_theme() -> str:
    theme = st.session_state.get(THEME_KEY, "light")
    return theme if theme in VALID_THEMES else "light"


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
    for mbsi_key, src_key in _MBSI_VAR_MAP.items():
        if src_key in palette:
            lines.append(f"  --{mbsi_key}: {palette[src_key]};")
    lines.append("}")
    return "\n".join(lines)


def _light_mode_widget_css() -> str:
    """Explicit Streamlit widget overrides — fixes white-on-white in day mode."""
    return """
.stApp[data-mbsi-theme="light"],
[data-mbsi-theme="light"] .stApp {
  background: var(--mbsi-bg) !important;
  color: var(--mbsi-text) !important;
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
  color: var(--mbsi-text) !important;
}
.stApp[data-mbsi-theme="light"] div[data-testid="stMetricLabel"],
.stApp[data-mbsi-theme="light"] small,
.stApp[data-mbsi-theme="light"] .stCaption {
  color: var(--mbsi-muted) !important;
}
.stApp[data-mbsi-theme="light"] .stButton > button {
  color: var(--mbsi-text) !important;
  background-color: var(--mbsi-surface-alt) !important;
  border: 1px solid var(--mbsi-border) !important;
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
  background-color: var(--mbsi-surface) !important;
  color: var(--mbsi-text) !important;
  border-color: var(--mbsi-border) !important;
}
.stApp[data-mbsi-theme="light"] div[data-baseweb="select"] span,
.stApp[data-mbsi-theme="light"] div[data-baseweb="input"] input {
  color: var(--mbsi-text) !important;
}
.stApp[data-mbsi-theme="light"] [data-testid="stDataFrame"],
.stApp[data-mbsi-theme="light"] [data-testid="stTable"] {
  color: var(--mbsi-text) !important;
}
.stApp[data-mbsi-theme="light"] [data-testid="stChatMessage"],
.stApp[data-mbsi-theme="light"] [data-testid="stChatMessageContent"] {
  color: var(--mbsi-text) !important;
  background: var(--mbsi-surface-alt) !important;
}
.stApp[data-mbsi-theme="light"] .saas-app div[data-testid="column"]:has(.saas-left-nav-anchor),
.stApp[data-mbsi-theme="light"] .saas-app div[data-testid="stHorizontalBlock"]:has(.saas-top-bar-anchor),
.stApp[data-mbsi-theme="light"] .saas-app div[data-testid="column"]:has(.saas-workspace-anchor),
.stApp[data-mbsi-theme="light"] .saas-app div[data-testid="column"]:has(.saas-drawer-anchor) {
  color: var(--mbsi-text) !important;
}
.stApp[data-mbsi-theme="light"] .saas-context-module {
  color: var(--mbsi-text) !important;
}
.stApp[data-mbsi-theme="light"] div[data-testid="stRadio"] label,
.stApp[data-mbsi-theme="light"] div[data-testid="stCheckbox"] label,
.stApp[data-mbsi-theme="light"] div[data-testid="stSelectbox"] label,
.stApp[data-mbsi-theme="light"] div[data-testid="stSlider"] label {
  color: var(--mbsi-text) !important;
}
.stApp[data-mbsi-theme="light"] [data-testid="stAlert"],
.stApp[data-mbsi-theme="light"] [data-baseweb="notification"] {
  color: var(--mbsi-text) !important;
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
        label = "Light" if theme == "dark" else "Dark"
        if st.button(f"{icon} {label}", key="theme_quick_toggle", use_container_width=True):
            set_theme("light" if theme == "dark" else "dark")
            st.rerun()
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("☀️ Light", key="theme_day_btn", type="primary" if theme == "light" else "secondary"):
                set_theme("light")
                st.rerun()
        with c2:
            if st.button("🌙 Dark", key="theme_night_btn", type="primary" if theme == "dark" else "secondary"):
                set_theme("dark")
                st.rerun()


def render_theme_settings() -> None:
    """Full theme picker for Settings workspace."""
    theme = get_theme()
    st.markdown("#### Appearance")
    choice = st.radio(
        "Color theme",
        options=["light", "dark"],
        format_func=lambda x: "☀️ Light — professional default" if x == "light" else "🌙 Dark — low-glare viewing",
        index=0 if theme == "light" else 1,
        key="settings_theme_radio",
        horizontal=True,
    )
    if choice != theme:
        set_theme(choice)
        st.rerun()
    if theme == "light":
        st.caption("Light mode uses clean white panels and high-contrast text.")
    else:
        st.caption("Dark mode uses refined dark panels for extended sessions.")
