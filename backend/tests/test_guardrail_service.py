from underlytics_api.schemas.structured_outputs import RiskAssessmentOutput
from underlytics_api.services.guardrail_service import (
    enforce_decision_guardrails,
    evaluate_decision_guardrails,
    validate_agent_output,
)


def test_validate_agent_output_accepts_valid_payload():
    result = validate_agent_output(
        "risk_assessment",
        {
            "score": 0.82,
            "confidence": 0.91,
            "decision": "low",
            "flags": [],
            "reasoning": "Disposable income supports the request.",
        },
    )
    assert isinstance(result, RiskAssessmentOutput)
    assert result.decision == "low"


def test_validate_agent_output_normalizes_scores_for_compatibility():
    result = validate_agent_output(
        "risk_assessment",
        {
            "score": "1.2",
            "confidence": -1,
            "decision": "medium",
            "flags": [],
            "reasoning": "Borderline affordability requires caution.",
        },
    )

    assert result.model_dump(exclude_none=True)["score"] == 1.0
    assert result.model_dump(exclude_none=True)["confidence"] == 0.0


def test_guardrail_prevents_approval_when_documents_missing():
    guardrail_result = evaluate_decision_guardrails(
        document_output={"decision": "documents_missing"},
        policy_output={"decision": "policy_match"},
        risk_output={"decision": "low"},
        fraud_output={"decision": "clear"},
        proposed_decision="approved",
    )

    assert guardrail_result.final_decision == "manual_review"
    assert guardrail_result.violations == ["missing_required_documents"]
    assert (
        enforce_decision_guardrails(
            document_output={"decision": "documents_missing"},
            policy_output={"decision": "policy_match"},
            risk_output={"decision": "low"},
            fraud_output={"decision": "clear"},
            proposed_decision="approved",
        )
        == "manual_review"
    )
