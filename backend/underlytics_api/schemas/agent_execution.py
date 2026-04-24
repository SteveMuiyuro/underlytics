from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EvaluationAgentOutput(BaseModel):
    score: float
    confidence: float
    decision: str
    flags: list[str]
    reasoning: str
    inputs_used: dict[str, Any] | None = None


WorkerName = Literal[
    "document_analysis",
    "policy_retrieval",
    "risk_assessment",
    "fraud_verification",
    "decision_summary",
]


class PlannerStepOutput(BaseModel):
    step_key: WorkerName
    step_type: Literal["worker"] = "worker"
    worker_name: WorkerName
    queue_name: str = "underwriting"
    priority: int
    dependencies: list[WorkerName] = Field(default_factory=list)
    input_context: dict[str, Any] = Field(default_factory=dict)


class PlannerPlanOutput(BaseModel):
    plan_version: str = "v1"
    planner_mode: str
    summary: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    steps: list[PlannerStepOutput]


class EmailAgentOutput(BaseModel):
    subject: str
    html_body: str
