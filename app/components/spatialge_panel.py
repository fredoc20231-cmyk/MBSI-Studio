"""Optional user-facing spatialGE 2.x analyses in the Study & Data workspace."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

import streamlit as st

from mbsi.integrations.spatialge import (
    SUPPORTED_OPERATIONS,
    prepare_spatialge_inputs,
    run_spatialge,
)


def _session_samples():
    """Collect only successfully ingested observed AnnData, never synthetic fallback."""
    samples = dict(st.session_state.get("sample_adatas") or {})
    if samples:
        return samples
    paths = st.session_state.get("sample_adata_paths") or {}
    if paths:
        import anndata as ad
        return {sid: ad.read_h5ad(path) for sid, path in paths.items() if path}
    single = st.session_state.get("adata")
    if single is not None:
        sid = (st.session_state.get("ingestion_result") or {}).get("sample_id") or "sample_1"
        return {str(sid): single}
    return {}


def render_spatialge_panel() -> None:
    """R-backed secondary engine. No implicit installs, no demo outputs."""
    with st.expander("Advanced spatialGE methods (optional R engine)", expanded=False):
        st.caption(
            "Executes FridleyLab spatialGE v2 in R, not a Python approximation. "
            "Requires installed Rscript and spatialGE. Outputs and original "
            "sample identities are preserved separately from MBSI core analyses."
        )
        ready = shutil.which("Rscript") is not None
        if not ready:
            st.warning("Rscript is not installed on this server. See docs/SPATIALGE_INTEGRATION.md.")
        st.write("Available upstream operations: " + ", ".join(sorted(SUPPORTED_OPERATIONS)))
        profile = st.selectbox(
            "Analysis profile",
            ("Spatial autocorrelation", "Spatial domains",
             "Spatial niches", "Gene-set enrichment", "Gene interpolation",
             "Custom method sequence"),
            key="spatialge_profile",
        )
        genes = st.text_input(
            "Gene symbols (comma separated, for autocorrelation/interpolation)",
            value="TP53",
            key="spatialge_genes",
        )
        gene_sets_json = ""
        if profile in ("Spatial niches", "Gene-set enrichment"):
            gene_sets_json = st.text_area(
                "Named gene sets (JSON): e.g. {\"T_cells\":[\"CD3D\",\"CD3E\"]}",
                value="{}",
                key="spatialge_genesets",
            )
        advanced = ""
        if profile == "Custom method sequence":
            advanced = st.text_area(
                "Sequence of operations as JSON",
                value=json.dumps([
                    {"method": "transform_data", "params": {"method": "log"}},
                    {"method": "SThet", "params": {"genes": ["TP53"], "method": ["moran", "geary"]}},
                ], indent=2),
                height=160,
                key="spatialge_custom",
            )
        limit = st.number_input(
            "Maximum total cells in dense TSV export (entries = genes × observations, per sample)",
            min_value=100000, max_value=50000000, value=10000000,
            step=1000000, key="spatialge_max_entries",
        )
        clicked = st.button(
            "Run spatialGE with real samples", key="spatialge_run", disabled=not ready,
        )
        if clicked:
            if st.session_state.get("using_synthetic_demo"):
                st.error("SpatialGE production analyses require real ingested samples.")
                return
            try:
                if profile == "Custom method sequence":
                    operations = json.loads(advanced)
                elif profile in ("Spatial niches", "Gene-set enrichment"):
                    sets = json.loads(gene_sets_json)
                    if not isinstance(sets, dict) or not sets:
                        raise ValueError("Supply at least one named gene set")
                    method = "STniche" if profile == "Spatial niches" else "STenrich"
                    operations = [
                        {"method": "transform_data", "params": {"method": "log"}},
                        {"method": method, "params": {"gene_sets": sets}},
                    ]
                    if method == "STniche":
                        operations.append({"method": "plot_stniche", "params": {"type": "clusters"}})
                elif profile == "Spatial domains":
                    operations = [
                        {"method": "transform_data", "params": {"method": "log"}},
                        {"method": "STclust", "params": {"ws": 0.025}},
                        {"method": "STplot", "params": {"ws": 0.025}},
                    ]
                else:
                    selected = [s.strip() for s in genes.split(",") if s.strip()]
                    if not selected:
                        raise ValueError("Select one or more gene symbols")
                    if profile == "Spatial autocorrelation":
                        operations = [
                            {"method": "transform_data", "params": {"method": "log"}},
                            {"method": "SThet", "params": {
                                "genes": selected, "method": ["moran", "geary"],
                            }},
                        ]
                    else:
                        operations = [
                            {"method": "transform_data", "params": {"method": "log"}},
                            {"method": "gene_interpolation", "params": {"genes": selected}},
                            {"method": "STplot_interpolation", "params": {"genes": selected}},
                        ]
                samples = _session_samples()
                if not samples:
                    raise ValueError("Upload and ingest real spatial samples first")
                destination = Path("data/outputs/spatialge") / uuid4().hex
                sample_table = st.session_state.get("sample_metadata")
                rows = (
                    sample_table.to_dict("records")
                    if hasattr(sample_table, "to_dict")
                    else sample_table if isinstance(sample_table, list) else []
                )
                sample_meta = {
                    str(row["sample_id"]): row for row in rows
                    if isinstance(row, dict) and row.get("sample_id")
                }
                with st.spinner("Running upstream spatialGE in R..."):
                    manifest = prepare_spatialge_inputs(
                        samples, destination, max_export_elements=int(limit),
                        sample_metadata=sample_meta,
                    )
                    summary = run_spatialge(manifest, operations)
                st.session_state["spatialge_last_run"] = {
                    "output_dir": str(destination / "results"), "summary": summary,
                }
                st.success("spatialGE completed; results saved with full R provenance.")
            except Exception as exc:
                st.error(f"spatialGE operation failed: {exc}")
        result = st.session_state.get("spatialge_last_run")
        if result:
            st.caption("Last spatialGE result directory: " + result["output_dir"])
            st.json(result["summary"])
