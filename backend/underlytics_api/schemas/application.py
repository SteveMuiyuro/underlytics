from datetime import datetime

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    applicant_user_id: str
    loan_product_id: str
    requested_amount: int
    requested_term_months: int
    loan_purpose: str | None = None
    monthly_income: int
    monthly_expenses: int
    existing_loan_obligations: int = 0
    employment_status: str | None = None
    employer_name: str | None = None
    bank_name: str | None = None
    account_type: str | None = None


class ApplicationResponse(BaseModel):
    id: str
    application_number: str
    applicant_user_id: str
    loan_product_id: str
    status: str
    requested_amount: int
    requested_term_months: int
    loan_purpose: str | None
    monthly_income: int
    monthly_expenses: int
    existing_loan_obligations: int
    employment_status: str | None
    employer_name: str | None
    bank_name: str | None
    account_type: str | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}