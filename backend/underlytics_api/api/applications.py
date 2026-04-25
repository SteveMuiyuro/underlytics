from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from underlytics_api.core.auth import (
    ActorContext,
    enforce_application_access,
    get_actor_context,
    require_authenticated_actor,
    require_registered_actor,
)
from underlytics_api.db.dependencies import get_db
from underlytics_api.models.agent_evaluation import AgentEvaluation
from underlytics_api.models.application import Application
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User
from underlytics_api.schemas.agent_evaluation import ApplicationAgentEvaluationResponse
from underlytics_api.schemas.application import ApplicationCreate, ApplicationResponse
from underlytics_api.schemas.workflow import WorkflowStatusResponse
from underlytics_api.services.workflow_dispatch_service import dispatch_underwriting_workflow
from underlytics_api.services.workflow_status_service import build_workflow_status

router = APIRouter(prefix="/api/applications", tags=["Applications"])

EMPLOYER_NAME_HIDDEN_STATUSES = {"self_employed", "unemployed"}


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


@router.get("", response_model=list[ApplicationResponse])
def list_applications(
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)
    require_registered_actor(actor)

    query = db.query(Application)
    if not actor.has_review_access:
        query = query.filter(Application.applicant_user_id == actor.backend_user_id)

    return query.order_by(Application.created_at.desc()).all()


@router.get("/stats")
def get_application_stats(
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)
    require_registered_actor(actor)

    base_query = db.query(Application)
    if not actor.has_review_access:
        base_query = base_query.filter(Application.applicant_user_id == actor.backend_user_id)

    total = base_query.with_entities(func.count(Application.id)).scalar()

    approved = base_query.filter(Application.status == "approved").with_entities(
        func.count(Application.id)
    ).scalar()

    rejected = base_query.filter(Application.status == "rejected").with_entities(
        func.count(Application.id)
    ).scalar()

    in_progress = base_query.filter(Application.status == "in_progress").with_entities(
        func.count(Application.id)
    ).scalar()

    submitted = base_query.filter(Application.status == "submitted").with_entities(
        func.count(Application.id)
    ).scalar()

    return {
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "in_progress": in_progress,
        "submitted": submitted,
    }


@router.get("/{application_number}", response_model=ApplicationResponse)
def get_application(
    application_number: str,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)
    require_registered_actor(actor)

    application = (
        db.query(Application)
        .filter(Application.application_number == application_number)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_application_access(
        actor=actor, applicant_user_id=application.applicant_user_id
    )

    return application


@router.get("/{application_number}/workflow-status", response_model=WorkflowStatusResponse)
def get_application_workflow_status(
    application_number: str,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)
    require_registered_actor(actor)

    application = (
        db.query(Application)
        .filter(Application.application_number == application_number)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_application_access(
        actor=actor, applicant_user_id=application.applicant_user_id
    )

    return build_workflow_status(db, application=application)


@router.get(
    "/{application_number}/evaluations",
    response_model=list[ApplicationAgentEvaluationResponse],
)
def get_application_evaluations(
    application_number: str,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)
    require_registered_actor(actor)

    application = (
        db.query(Application)
        .filter(Application.application_number == application_number)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_application_access(
        actor=actor, applicant_user_id=application.applicant_user_id
    )

    return (
        db.query(AgentEvaluation)
        .filter(AgentEvaluation.application_id == application.id)
        .order_by(AgentEvaluation.created_at.desc(), AgentEvaluation.agent_name.asc())
        .all()
    )


@router.post("", response_model=ApplicationResponse)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)
    require_registered_actor(actor)

    applicant = db.query(User).filter(User.id == payload.applicant_user_id).first()
    if not applicant:
        raise HTTPException(status_code=400, detail="Applicant user not found")

    product = db.query(LoanProduct).filter(LoanProduct.id == payload.loan_product_id).first()
    if not product:
        raise HTTPException(status_code=400, detail="Loan product not found")

    if actor.backend_user_id != payload.applicant_user_id:
        raise HTTPException(
            status_code=403,
            detail="Authenticated user cannot create applications for another applicant",
        )

    count = db.query(Application).count() + 1
    application_number = f"APP-{count:03d}"
    normalized_employment_status = _normalize_optional_text(payload.employment_status)
    normalized_existing_obligations = max(payload.existing_loan_obligations, 0)
    normalized_employer_name = _normalize_optional_text(payload.employer_name)
    normalized_bank_name = _normalize_optional_text(payload.bank_name)
    normalized_account_type = _normalize_optional_text(payload.account_type)

    if normalized_employment_status in EMPLOYER_NAME_HIDDEN_STATUSES:
        normalized_employer_name = None

    if normalized_existing_obligations <= 0:
        normalized_bank_name = None
        normalized_account_type = None

    application = Application(
        application_number=application_number,
        applicant_user_id=payload.applicant_user_id,
        loan_product_id=payload.loan_product_id,
        status="submitted",
        requested_amount=payload.requested_amount,
        requested_term_months=payload.requested_term_months,
        loan_purpose=payload.loan_purpose,
        monthly_income=payload.monthly_income,
        monthly_expenses=payload.monthly_expenses,
        existing_loan_obligations=normalized_existing_obligations,
        employment_status=normalized_employment_status,
        employer_name=normalized_employer_name,
        bank_name=normalized_bank_name,
        account_type=normalized_account_type,
        submitted_at=datetime.utcnow(),
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    if payload.auto_start_workflow:
        dispatch_underwriting_workflow(db, application.id)

    return application
