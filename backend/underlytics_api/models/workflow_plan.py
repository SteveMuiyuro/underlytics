from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from underlytics_api.models.base import Base


class WorkflowPlan(Base):
    __tablename__ = "workflow_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    application_id: Mapped[str] = mapped_column(
        String, ForeignKey("applications.id"), nullable=False
    )
    plan_version: Mapped[str] = mapped_column(String, nullable=False, default="v1")
    planner_mode: Mapped[str] = mapped_column(
        String, nullable=False, default="deterministic_foundation"
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="planned")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
