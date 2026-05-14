from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

UnderwritingAgentName = Literal[
    "document_analysis",
    "policy_retrieval",
    "risk_assessment",
    "fraud_verification",
    "decision_summary",
]

FinalDecision = Literal["approved", "rejected", "manual_review"]


class StructuredOutputModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class BaseUnderwritingAgentOutput(StructuredOutputModel):
    score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    flags: list[str] = Field(default_factory=list)
    reasoning: str
    inputs_used: dict[str, Any] | None = None

    @field_validator("score", "confidence", mode="before")
    @classmethod
    def normalize_unit_float(cls, value: Any) -> float:
        try:
            normalized = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("value must be numeric") from exc

        if normalized < 0:
            return 0.0
        if normalized > 1:
            return 1.0
        return normalized

    @field_validator("flags", mode="before")
    @classmethod
    def normalize_flags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("flags must be a list")
        if not all(isinstance(flag, str) for flag in value):
            raise ValueError("flags must contain only strings")
        return value

    @field_validator("reasoning")
    @classmethod
    def normalize_reasoning(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("reasoning must not be empty")
        return normalized


class DocumentAnalysisOutput(BaseUnderwritingAgentOutput):
    decision: Literal["documents_complete", "documents_missing"]
    missing_documents: list[str] | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)


class PolicyRetrievalOutput(BaseUnderwritingAgentOutput):
    decision: Literal["policy_match", "policy_mismatch"]
    violated_rules: list[str] | None = None
    manual_review_triggers: list[str] | None = None


class RiskAssessmentOutput(BaseUnderwritingAgentOutput):
    decision: Literal["low", "medium", "high"]
    debt_to_income_ratio: float | None = Field(default=None, ge=0)
    affordability: Literal["low", "medium", "high"] | None = None
    risk_factors: list[str] | None = None


class FraudVerificationOutput(BaseUnderwritingAgentOutput):
    decision: Literal["clear", "suspicious"]
    fraud_detected: bool | None = None
    fraud_signals: list[str] | None = None
    identity_match_score: float | None = Field(default=None, ge=0, le=1)


class DecisionSummaryOutput(BaseUnderwritingAgentOutput):
    decision: FinalDecision
    contributing_factors: list[str] | None = None
    guardrail_overrides: list[str] | None = None


UNDERWRITING_AGENT_OUTPUT_TYPES: dict[UnderwritingAgentName, type[BaseUnderwritingAgentOutput]] = {
    "document_analysis": DocumentAnalysisOutput,
    "policy_retrieval": PolicyRetrievalOutput,
    "risk_assessment": RiskAssessmentOutput,
    "fraud_verification": FraudVerificationOutput,
    "decision_summary": DecisionSummaryOutput,
}


def get_agent_output_model(agent_name: str) -> type[BaseUnderwritingAgentOutput]:
    try:
        return UNDERWRITING_AGENT_OUTPUT_TYPES[agent_name]  # type: ignore[index]
    except KeyError as exc:
        raise ValueError(f"Unsupported underwriting agent '{agent_name}'") from exc
