import json
from dataclasses import asdict, dataclass, field

from sqlalchemy.orm import Session

from underlytics_api.agents.prompts import PLANNER_PROMPT
from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument
from underlytics_api.schemas.agent_execution import PlannerPlanOutput
from underlytics_api.services.tracing_service import (
    ensure_trace_context,
    start_agent_observability,
)
from underlytics_api.services.underwriting_agent_service import _run_structured_agent

REQUIRED_DOCUMENT_TYPES = ("id_document", "payslip", "bank_statement")
PLANNER_TRACE_NAME = "underlytics-planner-agent"


@dataclass
class PlannedStep:
    step_key: str
    step_type: str
    worker_name: str
    queue_name: str
    priority: int
    dependencies: list[str] = field(default_factory=list)
    input_context: dict = field(default_factory=dict)


@dataclass
class WorkflowPlanDraft:
    plan_version: str
    planner_mode: str
    summary: str
    metadata: dict
    steps: list[PlannedStep]

    def to_json(self) -> str:
        return json.dumps(
            {
                "plan_version": self.plan_version,
                "planner_mode": self.planner_mode,
                "summary": self.summary,
                "metadata": self.metadata,
                "steps": [asdict(step) for step in self.steps],
            }
        )


def build_underwriting_plan(db: Session, application: Application) -> WorkflowPlanDraft:
    documents = (
        db.query(ApplicationDocument)
        .filter(ApplicationDocument.application_id == application.id)
        .all()
    )

    uploaded_types = sorted({document.document_type for document in documents})
    missing_types = sorted(set(REQUIRED_DOCUMENT_TYPES) - set(uploaded_types))

    shared_context = {
        "application_id": application.id,
        "application_number": application.application_number,
    }
    planner_input = {
        "application": {
            **shared_context,
            "requested_amount": application.requested_amount,
            "requested_term_months": application.requested_term_months,
            "loan_product_id": application.loan_product_id,
        },
        "required_document_types": list(REQUIRED_DOCUMENT_TYPES),
        "uploaded_document_types": uploaded_types,
        "missing_required_document_types": missing_types,
        "required_workers": [
            "document_analysis",
            "policy_retrieval",
            "risk_assessment",
            "fraud_verification",
            "decision_summary",
        ],
        "required_decision_summary_dependencies": [
            "document_analysis",
            "policy_retrieval",
            "risk_assessment",
            "fraud_verification",
        ],
    }
    planner_metadata = {
        "application_id": application.id,
        "application_number": application.application_number,
        "agent_name": PLANNER_PROMPT.agent_name,
        "model_provider": PLANNER_PROMPT.model_provider,
        "model_name": PLANNER_PROMPT.model_name,
        "prompt_version": PLANNER_PROMPT.prompt_version,
    }
    trace_context = ensure_trace_context(
        seed=f"planner:{application.id}",
        group_id=application.id,
    )
    with start_agent_observability(
        trace_name=PLANNER_TRACE_NAME,
        trace_context=trace_context,
        metadata=planner_metadata,
        input_payload=planner_input,
    ) as observation:
        try:
            planner_output = _run_structured_agent(
                prompt=PLANNER_PROMPT,
                scoped_input=planner_input,
                output_type=PlannerPlanOutput,
            )
            structured_plan = PlannerPlanOutput.model_validate(planner_output)
        except Exception as exc:
            observation.record_error(
                message=str(exc),
                data=planner_metadata,
            )
            raise

        required_workers = {
            "document_analysis",
            "policy_retrieval",
            "risk_assessment",
            "fraud_verification",
            "decision_summary",
        }
        planned_workers = {step.worker_name for step in structured_plan.steps}
        if planned_workers != required_workers:
            raise ValueError("Planner output must include each required worker exactly once")

        decision_summary_step = next(
            step for step in structured_plan.steps if step.worker_name == "decision_summary"
        )
        if set(decision_summary_step.dependencies) != {
            "document_analysis",
            "policy_retrieval",
            "risk_assessment",
            "fraud_verification",
        }:
            raise ValueError("Decision summary must depend on all specialist workers")

        observation.record_output(
            output=structured_plan.model_dump(exclude_none=True),
            metadata={
                **planner_metadata,
                "planned_workers": sorted(planned_workers),
            },
        )

    steps = [
        PlannedStep(
            step_key=step.step_key,
            step_type=step.step_type,
            worker_name=step.worker_name,
            queue_name=step.queue_name,
            priority=step.priority,
            dependencies=step.dependencies,
            input_context=step.input_context or shared_context,
        )
        for step in structured_plan.steps
    ]

    metadata = {
        **structured_plan.metadata,
        "missing_required_document_types": missing_types,
        "uploaded_document_types": uploaded_types,
        "planner_agent": {
            "model_provider": PLANNER_PROMPT.model_provider,
            "model_name": PLANNER_PROMPT.model_name,
            "prompt_version": PLANNER_PROMPT.prompt_version,
        },
    }

    return WorkflowPlanDraft(
        plan_version=structured_plan.plan_version,
        planner_mode=structured_plan.planner_mode,
        summary=structured_plan.summary,
        metadata=metadata,
        steps=steps,
    )
