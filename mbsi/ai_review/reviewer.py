"""Rule-based outcome Q&A — no external LLM."""

from __future__ import annotations

from typing import Any, Dict

from mbsi.ai_review.grounding import collect_grounded_outputs
from mbsi.ai_review.prompts import GUARDRAIL, TEMPLATES


def answer_outcome_question(question: str) -> str:
    q = (question or "").lower().strip()
    ctx = collect_grounded_outputs()
    reg = ctx.get("registered", {})
    n_fig = len(reg.get("figures", []))
    n_tbl = len(reg.get("tables", []))

    if not ctx.get("last_run") and n_fig == 0 and n_tbl == 0:
        return (
            f"{GUARDRAIL}\n\nNo pipeline outputs in session yet. "
            "Run Benchmark, Communication, TME, or Discovery first."
        )

    if any(w in q for w in ("benchmark", "leaderboard", "method", "pearson")):
        b = ctx.get("benchmark", {})
        return TEMPLATES["benchmark"].format(
            readiness=b.get("readiness_score", "N/A"),
            top=b.get("leaderboard_top", "N/A"),
        ) + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("communication", "pathway", "ligand", "receptor", "signaling")):
        c = ctx.get("communication", {})
        return TEMPLATES["communication"].format(pathway=c.get("top_pathway", "N/A")) + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("tme", "niche", "immune", "microenvironment")):
        t = ctx.get("tme", {})
        return TEMPLATES["tme"].format(count=t.get("niche_count", 0)) + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("discovery", "pipeline", "status")):
        d = ctx.get("discovery", {})
        return TEMPLATES["discovery"].format(status=d.get("status", "not run")) + f"\n\n{GUARDRAIL}"

    if "warning" in q:
        ws = ctx.get("warnings", [])
        return TEMPLATES["warnings"].format(n=len(ws), list="; ".join(ws[-3:]) or "none") + f"\n\n{GUARDRAIL}"

    if any(w in q for w in ("finding", "result", "outcome")):
        fs = ctx.get("findings", [])
        items = [f"{f.get('title')}: {f.get('detail')}" for f in fs[:3]]
        return TEMPLATES["findings"].format(n=len(fs), list="; ".join(items) or "none") + f"\n\n{GUARDRAIL}"

    return TEMPLATES["default"].format(
        last_run=ctx.get("last_run", "none"),
        n_fig=n_fig,
        n_tbl=n_tbl,
    ) + f"\n\n{GUARDRAIL}"
