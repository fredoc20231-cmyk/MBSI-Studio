"""Pathway tables and filters."""

import streamlit as st
import pandas as pd


def render_pathway_table(pathways: pd.DataFrame, filter_option: str = "All Pathways") -> None:
    df = pathways.copy()
    if filter_option != "All Pathways":
        df = df[df["pathway"].str.contains(filter_option.split("–")[0], case=False, na=False)]
    rows_html = "".join(
        f'<tr style="border-bottom:1px solid #22314a;">'
        f'<td style="padding:4px;color:#f4f7fb;">{row.pathway}</td>'
        f'<td style="padding:4px;text-align:right;color:#39d98a;">{row.probability:.2f}</td>'
        f"</tr>"
        for row in df.itertuples()
    )
    st.markdown(
        f"""
        <table class="mbsi-pathway-table" style="width:100%;font-size:0.72rem;border-collapse:collapse;">
        <thead>
        <tr style="color:#9aa7b8;border-bottom:1px solid #22314a;">
            <th style="text-align:left;padding:4px;">Pathway</th>
            <th style="text-align:right;padding:4px;">Probability</th>
        </tr>
        </thead>
        <tbody>{rows_html}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )
