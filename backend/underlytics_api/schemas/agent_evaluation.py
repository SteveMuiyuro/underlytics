from datetime import datetime

from pydantic import BaseModel


class ApplicationAgentEvaluationResponse(BaseModel):
    agent_name: str
    status: str
    schema_valid: bool
    guardrail_adjusted: bool
    decision: str | None
    final_decision: str | None
    tool_evidence_count: int
    completed_tool_evidence_count: int
    latency_ms: int | None
    model_provider: str | None
    model_name: str | None
    prompt_version: str | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
