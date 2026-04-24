from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from underlytics_api.agents.prompts.base import AgentPromptDefinition
from underlytics_api.models.agent_evaluation import AgentEvaluation
from underlytics_api.models.workflow_step import WorkflowStep
from underlytics_api.models.workflow_step_attempt import WorkflowStepAttempt


def _extract_tool_evidence(scoped_input: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not scoped_input:
        return []

    raw_input = scoped_input.get("input", scoped_input)
    tool_evidence = raw_input.get("tool_evidence", [])
    if not isinstance(tool_evidence, list):
        return []

    return [entry for entry in tool_evidence if isinstance(entry, dict)]


def _compute_latency_ms(attempt: WorkflowStepAttempt) -> int | None:
    if not attempt.started_at or not attempt.completed_at:
        return None

    return max(0, int((attempt.completed_at - attempt.started_at).total_seconds() * 1000))


def record_agent_evaluation(
    db: Session,
    *,
    step: WorkflowStep,
    attempt: WorkflowStepAttempt,
    prompt: AgentPromptDefinition | None,
    scoped_input: dict[str, Any] | None,
    output: dict[str, Any] | None,
    status: str,
    schema_valid: bool,
    proposed_decision: str | None = None,
    final_decision: str | None = None,
    error_message: str | None = None,
) -> AgentEvaluation:
    tool_evidence = _extract_tool_evidence(scoped_input)
    completed_tool_evidence_count = sum(
        1 for entry in tool_evidence if entry.get("status") == "completed"
    )

    decision = proposed_decision or (output.get("decision") if output else None)
    normalized_final_decision = final_decision or decision
    flags = output.get("flags", []) if output else []
    guardrail_adjusted = (
        bool(decision)
        and bool(normalized_final_decision)
        and decision != normalized_final_decision
    )

    evaluation = AgentEvaluation(
        workflow_step_attempt_id=attempt.id,
        workflow_step_id=step.id,
        application_id=step.application_id,
        agent_name=step.worker_name,
        status=status,
        schema_valid=schema_valid,
        guardrail_adjusted=guardrail_adjusted,
        score=output.get("score") if output else None,
        confidence=output.get("confidence") if output else None,
        decision=decision,
        final_decision=normalized_final_decision,
        flags_count=len(flags) if isinstance(flags, list) else 0,
        tool_evidence_count=len(tool_evidence),
        completed_tool_evidence_count=completed_tool_evidence_count,
        latency_ms=_compute_latency_ms(attempt),
        model_provider=prompt.model_provider if prompt else None,
        model_name=prompt.model_name if prompt else None,
        prompt_version=prompt.prompt_version if prompt else None,
        supports_mcp=prompt.supports_mcp if prompt else False,
        evaluation_json=json.dumps(
            {
                "allowed_tools": list(prompt.allowed_tools) if prompt else [],
                "tool_sources": [entry.get("source") for entry in tool_evidence],
                "tool_statuses": [entry.get("status") for entry in tool_evidence],
                "reasoning_length": len((output or {}).get("reasoning", "")),
                "captured_at": datetime.utcnow().isoformat(),
            }
        ),
        error_message=error_message,
    )
    db.add(evaluation)
    return evaluation
