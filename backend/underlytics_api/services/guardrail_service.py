from typing import Any

ALLOWED_AGENT_DECISIONS = {
    "document_analysis": {"documents_complete", "documents_missing"},
    "policy_retrieval": {"policy_match", "policy_mismatch"},
    "risk_assessment": {"low", "medium", "high"},
    "fraud_verification": {"clear", "suspicious"},
    "decision_summary": {"approved", "rejected", "manual_review"},
}

ALLOWED_FINAL_DECISIONS = {"approved", "rejected", "manual_review"}


def _normalize_unit_float(value: Any, *, field_name: str, agent_name: str) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{agent_name} output has invalid {field_name}") from exc

    if normalized < 0:
        return 0.0

    if normalized > 1:
        return 1.0

    return normalized


def validate_agent_output(agent_name: str, output: dict[str, Any]) -> None:
    required_fields = {"score", "confidence", "decision", "flags", "reasoning"}

    missing = required_fields - set(output.keys())
    if missing:
        raise ValueError(
            f"{agent_name} output missing required fields: {', '.join(sorted(missing))}"
        )

    score = _normalize_unit_float(
        output.get("score"),
        field_name="score",
        agent_name=agent_name,
    )
    confidence = _normalize_unit_float(
        output.get("confidence"),
        field_name="confidence",
        agent_name=agent_name,
    )

    output["score"] = score
    output["confidence"] = confidence

    decision = output.get("decision")
    flags = output.get("flags")
    reasoning = output.get("reasoning")

    if not isinstance(decision, str):
        raise ValueError(f"{agent_name} output has invalid decision")

    if decision not in ALLOWED_AGENT_DECISIONS.get(agent_name, set()):
        raise ValueError(f"{agent_name} output has unsupported decision '{decision}'")

    if not isinstance(flags, list):
        raise ValueError(f"{agent_name} output has invalid flags")

    if not all(isinstance(flag, str) for flag in flags):
        raise ValueError(f"{agent_name} output flags must all be strings")

    if not isinstance(reasoning, str) or not reasoning.strip():
        raise ValueError(f"{agent_name} output has invalid reasoning")


def enforce_decision_guardrails(
    *,
    document_output: dict[str, Any],
    policy_output: dict[str, Any],
    risk_output: dict[str, Any],
    fraud_output: dict[str, Any],
    proposed_decision: str,
) -> str:
    if proposed_decision not in ALLOWED_FINAL_DECISIONS:
        raise ValueError(f"Unsupported final decision '{proposed_decision}'")

    document_ok = document_output.get("decision") == "documents_complete"
    policy_ok = policy_output.get("decision") == "policy_match"
    risk_decision = risk_output.get("decision")
    fraud_clear = fraud_output.get("decision") == "clear"

    if proposed_decision == "approved":
        if not document_ok:
            return "manual_review"
        if not policy_ok:
            return "rejected"
        if not fraud_clear:
            return "manual_review"
        if risk_decision != "low":
            return "manual_review"
        return "approved"

    if proposed_decision == "rejected":
        return "rejected"

    return "manual_review"