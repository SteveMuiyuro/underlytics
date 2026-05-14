from typing import Any

from pydantic import ValidationError

from underlytics_api.schemas.guardrails import DecisionGuardrailInputs, GuardrailResult
from underlytics_api.schemas.structured_outputs import (
    BaseUnderwritingAgentOutput,
    get_agent_output_model,
)


def validate_agent_output(agent_name: str, output: dict[str, Any]) -> BaseUnderwritingAgentOutput:
    output_model = get_agent_output_model(agent_name)
    try:
        return output_model.model_validate(output)
    except ValidationError as exc:
        raise ValueError(f"{agent_name} output failed schema validation") from exc


def evaluate_decision_guardrails(
    *,
    document_output: dict[str, Any],
    policy_output: dict[str, Any],
    risk_output: dict[str, Any],
    fraud_output: dict[str, Any],
    proposed_decision: str,
) -> GuardrailResult:
    try:
        inputs = DecisionGuardrailInputs.model_validate(
            {
                "document_output": document_output,
                "policy_output": policy_output,
                "risk_output": risk_output,
                "fraud_output": fraud_output,
                "proposed_decision": proposed_decision,
            }
        )
    except ValidationError as exc:
        raise ValueError("Decision guardrail inputs failed schema validation") from exc

    violations: list[str] = []
    final_decision = inputs.proposed_decision

    if inputs.proposed_decision == "approved":
        if inputs.document_output.decision != "documents_complete":
            violations.append("missing_required_documents")
            final_decision = "manual_review"

        if inputs.policy_output.decision != "policy_match":
            violations.append("policy_mismatch")
            final_decision = "rejected"

        if inputs.fraud_output.decision != "clear" and final_decision != "rejected":
            violations.append("fraud_signal_detected")
            final_decision = "manual_review"

        if inputs.risk_output.decision != "low" and final_decision != "rejected":
            violations.append("risk_requires_review")
            final_decision = "manual_review"

    allowed = final_decision == inputs.proposed_decision

    if allowed and inputs.proposed_decision == "approved":
        explanation = (
            "Approval satisfies the deterministic document, policy, fraud, and risk guardrails."
        )
    elif allowed and inputs.proposed_decision == "rejected":
        explanation = "Rejected decision accepted by deterministic guardrails."
    elif allowed:
        explanation = "Manual review preserved by deterministic guardrails."
    else:
        explanation = (
            "Deterministic guardrails overrode the proposed decision because: "
            + ", ".join(violations)
        )

    return GuardrailResult(
        allowed=allowed,
        original_decision=inputs.proposed_decision,
        final_decision=final_decision,
        violations=violations,
        escalation_required=final_decision == "manual_review",
        explanation=explanation,
    )


def enforce_decision_guardrails(
    *,
    document_output: dict[str, Any],
    policy_output: dict[str, Any],
    risk_output: dict[str, Any],
    fraud_output: dict[str, Any],
    proposed_decision: str,
) -> str:
    return evaluate_decision_guardrails(
        document_output=document_output,
        policy_output=policy_output,
        risk_output=risk_output,
        fraud_output=fraud_output,
        proposed_decision=proposed_decision,
    ).final_decision
