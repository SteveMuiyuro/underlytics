from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from underlytics_api.models.base import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    application_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    applicant_user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    loan_product_id: Mapped[str] = mapped_column(
        String, ForeignKey("loan_products.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    requested_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    loan_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)

    monthly_income: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_expenses: Mapped[int] = mapped_column(Integer, nullable=False)
    existing_loan_obligations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    employment_status: Mapped[str | None] = mapped_column(String, nullable=True)
    employer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String, nullable=True)
    account_type: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )