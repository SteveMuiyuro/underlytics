from sqlalchemy.orm import Session

from underlytics_api.models.underwriting_job import UnderwritingJob
from underlytics_api.services.orchestrator_service import materialize_underwriting_plan
from underlytics_api.services.worker_service import run_workflow_plan


def create_underwriting_workflow(db: Session, application_id: str) -> UnderwritingJob:
    plan = materialize_underwriting_plan(db, application_id)
    return run_workflow_plan(db, plan)


def restart_underwriting_workflow(db: Session, application_id: str) -> UnderwritingJob:
    return create_underwriting_workflow(db, application_id)
