from underlytics_api.services.guardrail_service import (
    enforce_decision_guardrails,
    validate_agent_output,
)


def test_validate_agent_output_accepts_valid_payload():
    validate_agent_output(
        "risk_assessment",
        {
            "score": 0.82,
            "confidence": 0.91,
            "decision": "low",
            "flags": [],
            "reasoning": "Disposable income supports the request.",
        },
    )


def test_guardrail_prevents_approval_when_documents_missing():
    final_decision = enforce_decision_guardrails(
        document_output={"decision": "documents_missing"},
        policy_output={"decision": "policy_match"},
        risk_output={"decision": "low"},
        fraud_output={"decision": "clear"},
        proposed_decision="approved",
    )

    assert final_decision == "manual_review"
