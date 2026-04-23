from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from underlytics_api.models.base import Base


class ManualReviewCase(Base):
    __tablename__ = "manual_review_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    application_id: Mapped[str] = mapped_column(
        String, ForeignKey("applications.id"), nullable=False
    )
    workflow_plan_id: Mapped[str] = mapped_column(
        String, ForeignKey("workflow_plans.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    assigned_reviewer_user_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
