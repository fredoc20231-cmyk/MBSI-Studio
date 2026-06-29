"""AI review and evidence workflow."""

from __future__ import annotations

from typing import Any, List, Optional

from mbsi.schema.run import RunRecord
from mbsi.schema.workflow import WorkflowModule


def run_review_workflow(question: str, findings: Optional[List[Any]] = None) -> RunRecord:
    try:
        from mbsi.ai_review.reviewer import answer_outcome_question

        answer = answer_outcome_question(question)
        return RunRecord.success(
            module=WorkflowModule.AI_REVIEW.value,
            inputs={"question": question},
            outputs={"answer": answer, "findings_count": len(findings or [])},
        )
    except Exception as exc:
        return RunRecord.failed(WorkflowModule.AI_REVIEW.value, str(exc))
