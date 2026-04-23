from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from underlytics_api.core.auth import (
    ActorContext,
    enforce_application_access,
    get_actor_context,
    require_authenticated_actor,
    require_registered_actor,
)
from underlytics_api.db.dependencies import get_db
from underlytics_api.models.agent_run import AgentRun
from underlytics_api.models.application import Application
from underlytics_api.models.underwriting_job import UnderwritingJob
from underlytics_api.schemas.workflow import (
    AgentRunResponse,
    UnderwritingJobResponse,
)

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


@router.get(
    "/applications/{application_number}/job",
    response_model=UnderwritingJobResponse,
)
def get_underwriting_job(
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

    job = (
        db.query(UnderwritingJob)
        .filter(UnderwritingJob.application_id == application.id)
        .order_by(UnderwritingJob.created_at.desc())
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="Workflow job not found")

    return job


@router.get("/jobs/{job_id}/agent-runs", response_model=list[AgentRunResponse])
def get_agent_runs(
    job_id: str,
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
):
    require_authenticated_actor(actor)
    require_registered_actor(actor)

    job = db.query(UnderwritingJob).filter(UnderwritingJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Workflow job not found")

    application = db.query(Application).filter(Application.id == job.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    enforce_application_access(
        actor=actor, applicant_user_id=application.applicant_user_id
    )

    runs = (
        db.query(AgentRun)
        .filter(AgentRun.underwriting_job_id == job_id)
        .order_by(AgentRun.created_at.asc())
        .all()
    )

    return runs
