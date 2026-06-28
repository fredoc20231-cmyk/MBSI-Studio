"""Results Notebook UI — chronological registered outputs."""

from __future__ import annotations

import streamlit as st

from mbsi.reports.registry import get_notebook_entries, get_registered_outputs


def render_results_notebook(compact: bool = False) -> None:
    """Render notebook panel (full workspace or compact drawer snippet)."""
    entries = get_notebook_entries()
    reg = get_registered_outputs()

    if compact:
        st.markdown("**Notebook**")
        st.caption(f"{len(entries)} entries")
        if entries:
            for e in entries[-3:]:
                _render_entry_row(e)
        else:
            st.caption("Run analyses to populate the notebook.")
        if st.button("Open full notebook", key="open_notebook_from_drawer", use_container_width=True):
            st.session_state.active_module = "notebook"
            st.rerun()
        return

    st.markdown("### Results Notebook")
    st.caption("Chronological log of figures, tables, and findings from this session.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Figures", len(reg.get("figures", [])))
    c2.metric("Tables", len(reg.get("tables", [])))
    c3.metric("Findings", len(reg.get("findings", [])))

    if not entries:
        st.info("No notebook entries yet. Run Benchmark, Discovery, Communication, or TME to register outputs.")
        return

    st.markdown('<div class="saas-notebook-list">', unsafe_allow_html=True)
    for entry in reversed(entries):
        st.markdown('<div class="saas-notebook-entry">', unsafe_allow_html=True)
        _render_entry_row(entry, detailed=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_entry_row(entry: dict, detailed: bool = False) -> None:
    etype = entry.get("type", "item")
    icon = {"figure": "📊", "table": "📋", "finding": "💡"}.get(etype, "•")
    title = entry.get("title") or entry.get("text", "Untitled")
    module = entry.get("module", "—")
    ts = entry.get("timestamp", "")[:19].replace("T", " ")
    if detailed:
        st.markdown(f"**{icon} {title}**")
        st.caption(f"{module} · {etype} · {ts}")
        if etype == "finding":
            st.write(entry.get("text", ""))
        elif etype == "table":
            st.caption(f"Columns: {', '.join(entry.get('columns', [])[:6])} · {entry.get('rows', 0)} rows")
    else:
        st.caption(f"{icon} {title} ({module})")
