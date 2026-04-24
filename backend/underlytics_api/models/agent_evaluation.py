from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from underlytics_api.models.base import Base


class AgentEvaluation(Base):
    __tablename__ = "agent_evaluations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    workflow_step_attempt_id: Mapped[str] = mapped_column(
        String, ForeignKey("workflow_step_attempts.id"), nullable=False
    )
    workflow_step_id: Mapped[str] = mapped_column(
        String, ForeignKey("workflow_steps.id"), nullable=False
    )
    application_id: Mapped[str] = mapped_column(
        String, ForeignKey("applications.id"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    schema_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    guardrail_adjusted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    decision: Mapped[str | None] = mapped_column(String, nullable=True)
    final_decision: Mapped[str | None] = mapped_column(String, nullable=True)
    flags_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tool_evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_tool_evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String, nullable=True)
    supports_mcp: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evaluation_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
