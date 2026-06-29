"""Convert Seurat-like pipeline results to Finding + Evidence."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from mbsi.confidence.engine import score_finding
from mbsi.discovery.findings_builder import _attach_sample_context, _sample_context
from mbsi.discovery_model.entities import Finding
from mbsi.discovery_model.evidence import create_evidence
from mbsi.discovery_model.finding_store import FindingStore
from mbsi.discovery_model.ontology import FindingType


def build_seurat_evidence(
    results: Dict[str, Any],
    readiness: Optional[Dict[str, Any]] = None,
    run_id: str = "",
) -> Tuple[FindingStore, List[str]]:
    """Convert Seurat-like results to scored Finding + Evidence objects."""
    store = FindingStore()
    warnings: List[str] = results.get("warnings", [])

    qc_summary = results.get("qc_summary")
    if qc_summary is not None and hasattr(qc_summary, "empty") and not qc_summary.empty:
        n_pass = results.get("adata")
        n_obs = getattr(n_pass, "n_obs", 0) if n_pass is not None else 0
        ev = create_evidence(
            "seurat_like", "qc", "QC passed",
            description=f"{n_obs} spots/cells after QC filtering",
            value=n_obs,
        )
        store.add_evidence(ev)
        finding = Finding.create(
            title="QC filtering complete",
            summary=f"{n_obs} observations passed QC thresholds",
            finding_type=FindingType.UNKNOWN.value,
            module="spatial_analysis",
            evidence_ids=[ev.evidence_id],
        )
        score_finding(finding, [ev], {}, readiness)
        store.add(_attach_sample_context(finding, readiness, run_id=run_id))

    markers = results.get("markers")
    if markers is not None and hasattr(markers, "empty") and not markers.empty:
        top = markers.groupby("cluster", as_index=False).head(3)
        for _, row in top.iterrows():
            gene = row.get("gene", "")
            cluster = row.get("cluster", "")
            ev = create_evidence(
                "seurat_like", "marker", f"Cluster {cluster}: {gene}",
                description=f"logFC={row.get('logfoldchange', 0):.2f}, adj p={row.get('pval_adj', 1):.4f}",
                value=float(row.get("logfoldchange", 0)),
            )
            store.add_evidence(ev)
            finding = Finding.create(
                title=f"Marker {gene} in cluster {cluster}",
                summary=f"Cluster marker {gene} (logFC {row.get('logfoldchange', 0):.2f})",
                finding_type=FindingType.BIOMARKER.value,
                module="spatial_analysis",
                evidence_ids=[ev.evidence_id],
                metadata={"gene": gene, "cluster": str(cluster)},
            )
            score_finding(finding, [ev], {}, readiness)
            store.add(_attach_sample_context(finding, readiness, run_id=run_id))

    de_results = results.get("de_results")
    if de_results is not None and hasattr(de_results, "empty") and not de_results.empty:
        sig = de_results[de_results.get("pval_adj", de_results["pval"]) < 0.05].head(5)
        for _, row in sig.iterrows():
            gene = row.get("gene", "")
            ev = create_evidence(
                "seurat_like", "de", f"DE gene: {gene}",
                value=float(row.get("logfoldchange", 0)),
            )
            store.add_evidence(ev)
            finding = Finding.create(
                title=f"Differentially expressed: {gene}",
                summary=f"DE gene {gene} between groups",
                finding_type=FindingType.UNKNOWN.value,
                module="spatial_analysis",
                evidence_ids=[ev.evidence_id],
            )
            score_finding(finding, [ev], {}, readiness)
            store.add(_attach_sample_context(finding, readiness, run_id=run_id))

    ref_mapping = results.get("reference_mapping")
    if isinstance(ref_mapping, dict) and ref_mapping.get("mean_confidence"):
        conf = ref_mapping["mean_confidence"]
        ev = create_evidence(
            "seurat_like", "reference", "Reference mapping",
            description=f"Mean mapping confidence {conf:.2f}",
            value=conf,
        )
        store.add_evidence(ev)
        finding = Finding.create(
            title="Reference atlas mapping",
            summary=f"Query mapped to reference with mean confidence {conf:.2f}",
            finding_type=FindingType.UNKNOWN.value,
            module="spatial_analysis",
            evidence_ids=[ev.evidence_id],
        )
        score_finding(finding, [ev], {}, readiness)
        store.add(_attach_sample_context(finding, readiness, run_id=run_id))

    integration = results.get("integration")
    if isinstance(integration, dict) and integration.get("fallback"):
        warnings.append(integration["fallback"])

    return store, warnings
