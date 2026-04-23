import json

from sqlalchemy.orm import Session

from underlytics_api.models.application import Application
from underlytics_api.models.workflow_plan import WorkflowPlan
from underlytics_api.models.workflow_step import WorkflowStep
from underlytics_api.models.workflow_step_dependency import WorkflowStepDependency
from underlytics_api.services.planner_service import build_underwriting_plan


def _initial_step_status(step_key: str, dependency_count: int) -> str:
    if dependency_count > 0:
        return "blocked"
    if step_key == "document_analysis":
        return "pending"
    return "pending"


def materialize_underwriting_plan(
    db: Session, application_id: str, *, planner_mode: str = "deterministic_foundation"
) -> WorkflowPlan:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise ValueError("Application not found")

    existing_plans = (
        db.query(WorkflowPlan)
        .filter(
            WorkflowPlan.application_id == application.id,
            WorkflowPlan.status.in_(["planned", "running", "awaiting_review"]),
        )
        .all()
    )
    for existing_plan in existing_plans:
        existing_plan.status = "superseded"

    draft = build_underwriting_plan(db, application)
    if planner_mode != draft.planner_mode:
        draft.planner_mode = planner_mode

    plan = WorkflowPlan(
        application_id=application.id,
        plan_version=draft.plan_version,
        planner_mode=draft.planner_mode,
        status="planned",
        summary=draft.summary,
        plan_json=draft.to_json(),
    )

    db.add(plan)
    db.flush()

    step_ids_by_key: dict[str, str] = {}
    for drafted_step in draft.steps:
        step = WorkflowStep(
            workflow_plan_id=plan.id,
            application_id=application.id,
            step_key=drafted_step.step_key,
            step_type=drafted_step.step_type,
            worker_name=drafted_step.worker_name,
            status=_initial_step_status(
                drafted_step.step_key, len(drafted_step.dependencies)
            ),
            queue_name=drafted_step.queue_name,
            input_context_json=json.dumps(drafted_step.input_context),
            output_schema_version="v1",
            priority=drafted_step.priority,
        )
        db.add(step)
        db.flush()
        step_ids_by_key[drafted_step.step_key] = step.id

    for drafted_step in draft.steps:
        workflow_step_id = step_ids_by_key[drafted_step.step_key]
        for dependency_key in drafted_step.dependencies:
            db.add(
                WorkflowStepDependency(
                    workflow_step_id=workflow_step_id,
                    depends_on_step_id=step_ids_by_key[dependency_key],
                )
            )

    db.commit()
    db.refresh(plan)
    return plan


def get_ready_steps(db: Session, workflow_plan_id: str) -> list[WorkflowStep]:
    steps = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_plan_id == workflow_plan_id)
        .order_by(WorkflowStep.priority.asc(), WorkflowStep.created_at.asc())
        .all()
    )

    dependency_rows = (
        db.query(WorkflowStepDependency)
        .filter(
            WorkflowStepDependency.workflow_step_id.in_([step.id for step in steps])
        )
        .all()
    )

    completed_step_ids = {
        step.id for step in steps if step.status in {"completed", "skipped"}
    }
    dependencies_by_step: dict[str, list[str]] = {}
    for row in dependency_rows:
        dependencies_by_step.setdefault(row.workflow_step_id, []).append(
            row.depends_on_step_id
        )

    ready_steps: list[WorkflowStep] = []
    for step in steps:
        if step.status not in {"pending", "blocked"}:
            continue

        dependency_ids = dependencies_by_step.get(step.id, [])
        if all(dependency_id in completed_step_ids for dependency_id in dependency_ids):
            ready_steps.append(step)

    return ready_steps
