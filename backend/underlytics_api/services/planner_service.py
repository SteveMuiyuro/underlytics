import json
from dataclasses import asdict, dataclass, field

from sqlalchemy.orm import Session

from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument

REQUIRED_DOCUMENT_TYPES = ("id_document", "payslip", "bank_statement")


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

    summary = "Planner created deterministic underwriting workflow."
    if missing_types:
        summary = (
            "Planner created underwriting workflow with missing prerequisite documents; "
            "workflow should remain resumable until required uploads are complete."
        )

    shared_context = {
        "application_id": application.id,
        "application_number": application.application_number,
    }

    steps = [
        PlannedStep(
            step_key="document_analysis",
            step_type="worker",
            worker_name="document_analysis",
            queue_name="underwriting",
            priority=10,
            input_context={
                **shared_context,
                "required_document_types": list(REQUIRED_DOCUMENT_TYPES),
                "uploaded_document_types": uploaded_types,
            },
        ),
        PlannedStep(
            step_key="policy_retrieval",
            step_type="worker",
            worker_name="policy_retrieval",
            queue_name="underwriting",
            priority=20,
            input_context=shared_context,
        ),
        PlannedStep(
            step_key="risk_assessment",
            step_type="worker",
            worker_name="risk_assessment",
            queue_name="underwriting",
            priority=30,
            input_context=shared_context,
        ),
        PlannedStep(
            step_key="fraud_verification",
            step_type="worker",
            worker_name="fraud_verification",
            queue_name="underwriting",
            priority=40,
            input_context=shared_context,
        ),
        PlannedStep(
            step_key="decision_summary",
            step_type="worker",
            worker_name="decision_summary",
            queue_name="underwriting",
            priority=50,
            dependencies=[
                "document_analysis",
                "policy_retrieval",
                "risk_assessment",
                "fraud_verification",
            ],
            input_context=shared_context,
        ),
    ]

    return WorkflowPlanDraft(
        plan_version="v1",
        planner_mode="deterministic_foundation",
        summary=summary,
        metadata={
            "missing_required_document_types": missing_types,
            "uploaded_document_types": uploaded_types,
        },
        steps=steps,
    )
