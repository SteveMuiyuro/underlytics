from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from underlytics_api.core.auth import (
    ActorContext,
    get_actor_context,
    require_reviewer_actor,
)
from underlytics_api.db.dependencies import get_db
from underlytics_api.models.application import Application
from underlytics_api.models.manual_review_action import ManualReviewAction
from underlytics_api.models.manual_review_case import ManualReviewCase
from underlytics_api.models.workflow_plan import WorkflowPlan
from underlytics_api.schemas.manual_review import (
    ManualReviewActionCreate,
    ManualReviewActionResponse,
    ManualReviewCaseDetailResponse,
    ManualReviewCaseSummaryResponse,
)
from underlytics_api.services.notification_service import (
    send_manual_review_completed_notification,
)

router = APIRouter(prefix="/api/manual-review", tags=["Manual Review"])

RESOLUTION_ACTIONS = {"approve": "approved", "reject": "rejected"}
ALLOWED_ACTIONS = {"assign", "note", *RESOLUTION_ACTIONS.keys()}


def _get_case_or_404(db: Session, case_id: str) -> ManualReviewCase:
    case = db.query(ManualReviewCase).filter(ManualReviewCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Manual review case not found")
    return case


def _get_application_or_404(db: Session, application_id: str) -> Application:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


def _get_plan_or_404(db: Session, workflow_plan_id: str) -> WorkflowPlan:
    plan = db.query(WorkflowPlan).filter(WorkflowPlan.id == workflow_plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Workflow plan not found")
    return plan


def _serialize_case(
    *,
    case: ManualReviewCase,
    application: Application,
    workflow_plan: WorkflowPlan,
    actions: list[ManualReviewAction] | None = None,
) -> ManualReviewCaseSummaryResponse | ManualReviewCaseDetailResponse:
    payload = {
        "id": case.id,
        "application_id": case.application_id,
        "application_number": application.application_number,
        "application_status": application.status,
        "requested_amount": application.requested_amount,
        "applicant_user_id": application.applicant_user_id,
        "workflow_plan_id": case.workflow_plan_id,
        "workflow_plan_status": workflow_plan.status,
        "status": case.status,
        "reason": case.reason,
        "assigned_reviewer_user_id": case.assigned_reviewer_user_id,
        "created_at": case.created_at,
        "resolved_at": case.resolved_at,
    }

    if actions is None:
        return ManualReviewCaseSummaryResponse(**payload)

    return ManualReviewCaseDetailResponse(
        **payload,
        actions=[
            ManualReviewActionResponse.model_validate(action)
            for action in actions
        ],
    )


@router.get("/cases", response_model=list[ManualReviewCaseSummaryResponse])
def list_manual_review_cases(
    status: str | None = Query(default="open"),
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_reviewer_actor(actor)

    query = db.query(ManualReviewCase).order_by(
        ManualReviewCase.resolved_at.is_not(None),
        ManualReviewCase.created_at.desc(),
    )
    if status:
        query = query.filter(ManualReviewCase.status == status)

    cases = query.all()
    if not cases:
        return []

    application_ids = {case.application_id for case in cases}
    workflow_plan_ids = {case.workflow_plan_id for case in cases}

    applications = {
        application.id: application
        for application in db.query(Application)
        .filter(Application.id.in_(application_ids))
        .all()
    }
    workflow_plans = {
        plan.id: plan
        for plan in db.query(WorkflowPlan)
        .filter(WorkflowPlan.id.in_(workflow_plan_ids))
        .all()
    }

    return [
        _serialize_case(
            case=case,
            application=applications[case.application_id],
            workflow_plan=workflow_plans[case.workflow_plan_id],
        )
        for case in cases
        if case.application_id in applications and case.workflow_plan_id in workflow_plans
    ]


@router.get("/cases/{case_id}", response_model=ManualReviewCaseDetailResponse)
def get_manual_review_case(
    case_id: str,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_reviewer_actor(actor)

    case = _get_case_or_404(db, case_id)
    application = _get_application_or_404(db, case.application_id)
    workflow_plan = _get_plan_or_404(db, case.workflow_plan_id)
    actions = (
        db.query(ManualReviewAction)
        .filter(ManualReviewAction.manual_review_case_id == case.id)
        .order_by(ManualReviewAction.created_at.desc())
        .all()
    )

    return _serialize_case(
        case=case,
        application=application,
        workflow_plan=workflow_plan,
        actions=actions,
    )


@router.post("/cases/{case_id}/actions", response_model=ManualReviewCaseDetailResponse)
def create_manual_review_action(
    case_id: str,
    payload: ManualReviewActionCreate,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_reviewer_actor(actor)

    if payload.action not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail="Unsupported manual review action")

    case = _get_case_or_404(db, case_id)
    application = _get_application_or_404(db, case.application_id)
    workflow_plan = _get_plan_or_404(db, case.workflow_plan_id)

    if case.assigned_reviewer_user_id and case.assigned_reviewer_user_id != actor.backend_user_id:
        raise HTTPException(
            status_code=409,
            detail="Manual review case is assigned to another reviewer",
        )

    if payload.action in {"assign", *RESOLUTION_ACTIONS.keys()} and case.status != "open":
        raise HTTPException(
            status_code=409,
            detail="Resolved manual review cases cannot be modified",
        )

    if not case.assigned_reviewer_user_id:
        case.assigned_reviewer_user_id = actor.backend_user_id

    old_decision = application.status
    new_decision = None
    note = (payload.note or "").strip()

    if payload.action == "assign":
        note = note or "Claimed manual review case"
    elif payload.action == "note":
        if not note:
            raise HTTPException(status_code=400, detail="A note is required")
    else:
        if not note:
            raise HTTPException(
                status_code=400,
                detail="A reviewer note is required for resolution",
            )

        new_decision = RESOLUTION_ACTIONS[payload.action]
        application.status = new_decision
        workflow_plan.status = "completed"
        case.status = "resolved"
        case.resolved_at = datetime.utcnow()

    action = ManualReviewAction(
        manual_review_case_id=case.id,
        reviewer_user_id=actor.backend_user_id,
        action=payload.action,
        note=note,
        old_decision=old_decision,
        new_decision=new_decision,
    )
    db.add(action)
    db.add(case)
    db.add(application)
    db.add(workflow_plan)
    db.commit()

    db.refresh(case)

    if new_decision is not None:
        send_manual_review_completed_notification(db, manual_review_case_id=case.id)

    refreshed_actions = (
        db.query(ManualReviewAction)
        .filter(ManualReviewAction.manual_review_case_id == case.id)
        .order_by(ManualReviewAction.created_at.desc())
        .all()
    )

    return _serialize_case(
        case=case,
        application=application,
        workflow_plan=workflow_plan,
        actions=refreshed_actions,
    )
