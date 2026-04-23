from datetime import datetime

from pydantic import BaseModel


class AgentOutputResponse(BaseModel):
    id: str
    agent_run_id: str
    application_id: str
    agent_name: str
    score: float | None
    confidence: float | None
    decision: str | None
    flags: str | None
    reasoning: str | None
    output_json: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}