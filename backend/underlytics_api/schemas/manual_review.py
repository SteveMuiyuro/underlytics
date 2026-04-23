from datetime import datetime

from pydantic import BaseModel


class ManualReviewActionCreate(BaseModel):
    action: str
    note: str | None = None


class ManualReviewActionResponse(BaseModel):
    id: str
    manual_review_case_id: str
    reviewer_user_id: str
    action: str
    note: str
    old_decision: str | None
    new_decision: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ManualReviewCaseSummaryResponse(BaseModel):
    id: str
    application_id: str
    application_number: str
    application_status: str
    requested_amount: int
    applicant_user_id: str
    workflow_plan_id: str
    workflow_plan_status: str
    status: str
    reason: str
    assigned_reviewer_user_id: str | None
    created_at: datetime
    resolved_at: datetime | None


class ManualReviewCaseDetailResponse(ManualReviewCaseSummaryResponse):
    actions: list[ManualReviewActionResponse]
