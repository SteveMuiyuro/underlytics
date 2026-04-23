from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from underlytics_api.models.base import Base


class ManualReviewAction(Base):
    __tablename__ = "manual_review_actions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    manual_review_case_id: Mapped[str] = mapped_column(
        String, ForeignKey("manual_review_cases.id"), nullable=False
    )
    reviewer_user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    old_decision: Mapped[str | None] = mapped_column(String, nullable=True)
    new_decision: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
