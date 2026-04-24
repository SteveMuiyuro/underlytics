from __future__ import annotations

from sqlalchemy.orm import Session

from underlytics_api.models.agent_output import AgentOutput
from underlytics_api.models.agent_run import AgentRun
from underlytics_api.models.application import Application
from underlytics_api.models.underwriting_job import UnderwritingJob
from underlytics_api.models.workflow_plan import WorkflowPlan
from underlytics_api.models.workflow_step import WorkflowStep
from underlytics_api.schemas.workflow import (
    WorkflowStatusAgentResponse,
    WorkflowStatusResponse,
)

AGENT_ORDER = [
    "planner",
    "document_analysis",
    "policy_retrieval",
    "risk_assessment",
    "fraud_verification",
    "decision_summary",
]

AGENT_META: dict[str, dict[str, str]] = {
    "planner": {
        "label": "Planner Agent",
        "snippet": "Preparing your underwriting workflow.",
    },
    "document_analysis": {
        "label": "Document Analysis",
        "snippet": "Checking uploaded documents and required files.",
    },
    "policy_retrieval": {
        "label": "Policy Retrieval",
        "snippet": "Comparing your request against product rules.",
    },
    "risk_assessment": {
        "label": "Risk Assessment",
        "snippet": "Reviewing income, expenses, and affordability.",
    },
    "fraud_verification": {
        "label": "Fraud Verification",
        "snippet": "Checking for unusual application signals.",
    },
    "decision_summary": {
        "label": "Decision Summary",
        "snippet": "Combining all agent findings into a final recommendation.",
    },
}

PROGRESS_BY_STAGE = {
    "planner": 10,
    "document_analysis": 25,
    "policy_retrieval": 40,
    "risk_assessment": 55,
    "fraud_verification": 70,
    "decision_summary": 90,
}

FINAL_APPLICATION_STATUSES = {"approved", "rejected", "manual_review"}


def _normalize_agent_status(status: str | None) -> str:
    if status in {"completed", "failed", "running", "pending"}:
        return status
    if status in {"blocked", "planned"}:
        return "pending"
    if status == "awaiting_review":
        return "completed"
    return "pending"


def _build_output_map(db: Session, *, application_id: str) -> dict[str, AgentOutput]:
    outputs = (
        db.query(AgentOutput)
        .filter(AgentOutput.application_id == application_id)
        .order_by(AgentOutput.created_at.desc())
        .all()
    )

    latest_by_agent: dict[str, AgentOutput] = {}
    for output in outputs:
        latest_by_agent.setdefault(output.agent_name, output)

    return latest_by_agent


def _build_step_map(db: Session, *, workflow_plan_id: str | None) -> dict[str, WorkflowStep]:
    if not workflow_plan_id:
        return {}

    steps = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_plan_id == workflow_plan_id)
        .order_by(WorkflowStep.priority.asc(), WorkflowStep.created_at.asc())
        .all()
    )
    return {step.worker_name: step for step in steps}


def _build_run_map(db: Session, *, underwriting_job_id: str | None) -> dict[str, AgentRun]:
    if not underwriting_job_id:
        return {}

    runs = (
        db.query(AgentRun)
        .filter(AgentRun.underwriting_job_id == underwriting_job_id)
        .order_by(AgentRun.created_at.asc())
        .all()
    )
    return {run.agent_name: run for run in runs}


def _resolve_planner_status(
    *,
    application: Application,
    plan: WorkflowPlan | None,
    job: UnderwritingJob | None,
) -> str:
    if plan:
        return "completed"
    if job and job.status == "failed":
        return "failed"
    if application.status in {"submitted", "in_progress"}:
        return "running"
    return "pending"


def _resolve_worker_status(
    *,
    step: WorkflowStep | None,
    run: AgentRun | None,
) -> str:
    if step:
        return _normalize_agent_status(step.status)
    if run:
        return _normalize_agent_status(run.status)
    return "pending"


def _resolve_current_stage(
    agents: list[WorkflowStatusAgentResponse],
    *,
    overall_status: str,
) -> str:
    if overall_status == "failed":
        failed_agent = next((agent for agent in agents if agent.status == "failed"), None)
        return failed_agent.name if failed_agent else "planner"

    running_agent = next((agent for agent in agents if agent.status == "running"), None)
    if running_agent:
        return running_agent.name

    pending_agent = next((agent for agent in agents if agent.status == "pending"), None)
    if pending_agent:
        return pending_agent.name

    return "decision_summary"


def _resolve_progress(
    *,
    agents: list[WorkflowStatusAgentResponse],
    redirect_ready: bool,
) -> int:
    if redirect_ready:
        return 100

    completed_progress = [
        PROGRESS_BY_STAGE[agent.name]
        for agent in agents
        if agent.name in PROGRESS_BY_STAGE and agent.status == "completed"
    ]

    if completed_progress:
        return max(completed_progress)

    planner_agent = next((agent for agent in agents if agent.name == "planner"), None)
    if planner_agent and planner_agent.status in {"running", "completed"}:
        return PROGRESS_BY_STAGE["planner"]

    return 10


def build_workflow_status(
    db: Session,
    *,
    application: Application,
) -> WorkflowStatusResponse:
    latest_plan = (
        db.query(WorkflowPlan)
        .filter(WorkflowPlan.application_id == application.id)
        .order_by(WorkflowPlan.created_at.desc())
        .first()
    )
    latest_job = (
        db.query(UnderwritingJob)
        .filter(UnderwritingJob.application_id == application.id)
        .order_by(UnderwritingJob.created_at.desc())
        .first()
    )
    output_map = _build_output_map(db, application_id=application.id)
    step_map = _build_step_map(db, workflow_plan_id=latest_plan.id if latest_plan else None)
    run_map = _build_run_map(db, underwriting_job_id=latest_job.id if latest_job else None)

    agents: list[WorkflowStatusAgentResponse] = []
    for agent_name in AGENT_ORDER:
        meta = AGENT_META[agent_name]
        output = output_map.get(agent_name)

        if agent_name == "planner":
            status = _resolve_planner_status(
                application=application,
                plan=latest_plan,
                job=latest_job,
            )
            reasoning = latest_plan.summary if latest_plan else None
            decision = None
        else:
            status = _resolve_worker_status(
                step=step_map.get(agent_name),
                run=run_map.get(agent_name),
            )
            reasoning = output.reasoning if output else None
            decision = output.decision if output else None

        agents.append(
            WorkflowStatusAgentResponse(
                name=agent_name,
                label=meta["label"],
                status=status,
                snippet=meta["snippet"],
                reasoning=reasoning,
                decision=decision,
            )
        )

    failed = (
        (latest_plan is not None and latest_plan.status == "failed")
        or (latest_job is not None and latest_job.status == "failed")
        or any(agent.status == "failed" for agent in agents)
    )
    decision_completed = any(
        agent.name == "decision_summary" and agent.status == "completed" for agent in agents
    )
    redirect_ready = decision_completed and application.status in FINAL_APPLICATION_STATUSES

    if failed:
        status = "failed"
    elif redirect_ready:
        status = "completed"
    else:
        status = "processing"

    return WorkflowStatusResponse(
        application_number=application.application_number,
        status=status,
        progress=_resolve_progress(agents=agents, redirect_ready=redirect_ready),
        current_stage=_resolve_current_stage(agents, overall_status=status),
        agents=agents,
    )
