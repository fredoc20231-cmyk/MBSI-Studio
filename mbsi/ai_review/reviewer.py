"""Rule-based outcome Q&A — grounded on findings graph."""

from __future__ import annotations

from typing import Any, Dict

from mbsi.ai_review.grounding import collect_grounded_outputs, get_finding_context
from mbsi.ai_review.prompts import GUARDRAIL, TEMPLATES


def answer_outcome_question(question: str) -> str:
    q = (question or "").lower().strip()
    ctx = collect_grounded_outputs()
    reg = ctx.get("registered", {})
    n_fig = len(reg.get("figures", []))
    n_tbl = len(reg.get("tables", []))
    dos_findings = ctx.get("findings", [])

    if not ctx.get("last_run") and not dos_findings and n_fig == 0 and n_tbl == 0:
        return (
            f"{GUARDRAIL}\n\nNo pipeline outputs in session yet. "
            "Run Benchmark, Communication, TME, or Discovery first."
        )

    if any(w in q for w in ("confidence", "high confidence", "moderate")):
        top = sorted(dos_findings, key=lambda f: f.get("confidence_score", 0), reverse=True)[:3]
        items = [f"{f.get('title')} ({f.get('confidence_level')}, {f.get('confidence_score', 0):.0f})" for f in top]
        return TEMPLATES["confidence"].format(list="; ".join(items) or "none") + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("evidence", "proof", "support")):
        ev = ctx.get("evidence", [])[:5]
        items = [f"{e.get('title')} ({e.get('evidence_type')})" for e in ev]
        return TEMPLATES["evidence"].format(n=len(ev), list="; ".join(items) or "none") + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("validation", "validate", "rt-pcr", "if", "ihc")):
        recs = ctx.get("validation_recommendations", [])[:3]
        items = []
        for r in recs:
            items.append(f"{r.get('title')}: {r.get('recommendations', [''])[0]}")
        return TEMPLATES["validation"].format(list="; ".join(items) or "Run discovery first") + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("graph", "related", "path", "outcome")):
        if dos_findings:
            fid = dos_findings[0].get("finding_id", "")
            path_ctx = get_finding_context(fid)
            path_str = " → ".join(p["step"] for p in path_ctx.get("path", []))
            related = ", ".join(path_ctx.get("related", [])[:3]) or "none"
            return TEMPLATES["graph"].format(path=path_str, related=related) + f"\n\n{GUARDRAIL}"
        return TEMPLATES["graph"].format(path="none", related="none") + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("benchmark", "leaderboard", "method", "pearson")):
        b = ctx.get("benchmark", {})
        support = b.get("benchmark_support", 0)
        return TEMPLATES["benchmark"].format(
            readiness=b.get("readiness_score", "N/A"),
            top=b.get("leaderboard_top", "N/A"),
            support=f"{support:.0f}%",
        ) + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("communication", "pathway", "ligand", "receptor", "signaling")):
        c = ctx.get("communication", {})
        return TEMPLATES["communication"].format(pathway=c.get("top_pathway", "N/A")) + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("tme", "niche", "immune", "microenvironment")):
        t = ctx.get("tme", {})
        return TEMPLATES["tme"].format(count=t.get("niche_count", 0)) + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("discovery", "pipeline", "status")):
        d = ctx.get("discovery", {})
        return TEMPLATES["discovery"].format(
            status=d.get("status", "not run"),
            n_findings=d.get("n_findings", len(dos_findings)),
        ) + f"\n\n{GUARDRAIL}"

    if "warning" in q:
        ws = ctx.get("warnings", [])
        return TEMPLATES["warnings"].format(n=len(ws), list="; ".join(ws[-3:]) or "none") + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("finding", "result", "outcome", "top")):
        items = [
            f"{f.get('title')} [{f.get('confidence_level', '?')}, {f.get('confidence_score', 0):.0f}]: {f.get('summary', '')[:80]}"
            for f in sorted(dos_findings, key=lambda x: x.get("confidence_score", 0), reverse=True)[:3]
        ]
        return TEMPLATES["findings"].format(n=len(dos_findings), list="; ".join(items) or "none") + f"\n\n{GUARDRAIL}"

    return TEMPLATES["default"].format(
        last_run=ctx.get("last_run", "none"),
        n_fig=n_fig,
        n_tbl=n_tbl,
        n_findings=len(dos_findings),
    ) + f"\n\n{GUARDRAIL}"
