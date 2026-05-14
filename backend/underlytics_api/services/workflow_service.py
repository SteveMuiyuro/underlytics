from sqlalchemy.orm import Session

from underlytics_api.models.application import Application
from underlytics_api.models.underwriting_job import UnderwritingJob
from underlytics_api.services.orchestrator_service import materialize_underwriting_plan
from underlytics_api.services.worker_service import run_workflow_plan

FINAL_APPLICATION_STATUSES = {"approved", "rejected", "manual_review"}
ACTIVE_JOB_STATUSES = {"pending", "running"}


def _load_application_for_workflow(
    db: Session,
    *,
    application_id: str,
) -> Application:
    application = (
        db.query(Application).filter(Application.id == application_id).with_for_update().first()
    )
    if not application:
        raise ValueError("Application not found")
    return application


def _latest_underwriting_job(
    db: Session,
    *,
    application_id: str,
) -> UnderwritingJob | None:
    return (
        db.query(UnderwritingJob)
        .filter(UnderwritingJob.application_id == application_id)
        .order_by(UnderwritingJob.created_at.desc())
        .first()
    )


def create_underwriting_workflow(
    db: Session,
    application_id: str,
    *,
    force_restart: bool = False,
) -> UnderwritingJob:
    application = _load_application_for_workflow(db, application_id=application_id)
    latest_job = _latest_underwriting_job(db, application_id=application_id)

    if not force_restart and latest_job and latest_job.status in ACTIVE_JOB_STATUSES:
        return latest_job

    if (
        not force_restart
        and latest_job
        and latest_job.status == "completed"
        and application.status in FINAL_APPLICATION_STATUSES
    ):
        return latest_job

    plan = materialize_underwriting_plan(db, application_id)
    return run_workflow_plan(db, plan)


def restart_underwriting_workflow(db: Session, application_id: str) -> UnderwritingJob:
    return create_underwriting_workflow(db, application_id, force_restart=True)
