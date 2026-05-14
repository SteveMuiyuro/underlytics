from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from underlytics_api.schemas.structured_outputs import FinalDecision


class DocumentDecisionInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision: Literal["documents_complete", "documents_missing"]


class PolicyDecisionInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision: Literal["policy_match", "policy_mismatch"]


class RiskDecisionInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision: Literal["low", "medium", "high"]


class FraudDecisionInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    decision: Literal["clear", "suspicious"]


class DecisionGuardrailInputs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_output: DocumentDecisionInput
    policy_output: PolicyDecisionInput
    risk_output: RiskDecisionInput
    fraud_output: FraudDecisionInput
    proposed_decision: FinalDecision


class GuardrailResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    original_decision: FinalDecision | None = None
    final_decision: FinalDecision
    violations: list[str] = Field(default_factory=list)
    escalation_required: bool
    explanation: str
