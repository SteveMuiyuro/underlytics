from datetime import datetime

from pydantic import BaseModel


class UnderwritingJobResponse(BaseModel):
    id: str
    application_id: str
    status: str
    current_step: str | None
    started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentRunResponse(BaseModel):
    id: str
    underwriting_job_id: str
    application_id: str
    agent_name: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None
    retry_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}