from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.models.agent_output import AgentOutput
from underlytics_api.models.application import Application
from underlytics_api.models.base import Base
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User
from underlytics_api.models.workflow_plan import WorkflowPlan
from underlytics_api.models.workflow_step import WorkflowStep
from underlytics_api.services.workflow_status_service import build_workflow_status


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_application(db: Session) -> Application:
    user = User(
        clerk_user_id="clerk-status-user",
        role="applicant",
        email="status@example.com",
        full_name="Status Example",
    )
    product = LoanProduct(
        code="personal",
        name="Personal Loan",
        description="Personal financing",
        min_amount=1000,
        max_amount=10000,
        min_term_months=3,
        max_term_months=24,
        is_active=True,
    )
    db.add_all([user, product])
    db.commit()
    db.refresh(user)
    db.refresh(product)

    application = Application(
        application_number="APP-STATUS-001",
        applicant_user_id=user.id,
        loan_product_id=product.id,
        status="submitted",
        requested_amount=5000,
        requested_term_months=12,
        monthly_income=3000,
        monthly_expenses=900,
        existing_loan_obligations=250,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def test_workflow_status_defaults_to_planner_running_before_plan_exists():
    db = make_session()

    try:
        application = seed_application(db)
        status = build_workflow_status(db, application=application)
    finally:
        db.close()

    assert status.status == "processing"
    assert status.progress == 10
    assert status.current_stage == "planner"
    assert status.agents[0].name == "planner"
    assert status.agents[0].status == "running"


def test_workflow_status_marks_completed_when_decision_summary_is_done():
    db = make_session()

    try:
        application = seed_application(db)
        application.status = "manual_review"
        db.add(application)
        db.commit()

        plan = WorkflowPlan(
            application_id=application.id,
            plan_version="v1",
            planner_mode="deterministic_foundation",
            status="awaiting_review",
            summary="Planner completed workflow and escalated to manual review.",
            plan_json="{}",
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        for index, worker_name in enumerate(
            [
                "document_analysis",
                "policy_retrieval",
                "risk_assessment",
                "fraud_verification",
                "decision_summary",
            ],
            start=1,
        ):
            db.add(
                WorkflowStep(
                    workflow_plan_id=plan.id,
                    application_id=application.id,
                    step_key=worker_name,
                    step_type="worker",
                    worker_name=worker_name,
                    status="completed",
                    queue_name="underwriting",
                    input_context_json="{}",
                    priority=index * 10,
                    decision="manual_review" if worker_name == "decision_summary" else None,
                )
            )

        db.add(
            AgentOutput(
                agent_run_id="run-decision-summary",
                application_id=application.id,
                agent_name="decision_summary",
                score=0.55,
                confidence=0.8,
                decision="manual_review",
                flags='["missing_documents"]',
                reasoning="Additional review is required before a final decision.",
                output_json="{}",
            )
        )
        db.commit()

        status = build_workflow_status(db, application=application)
    finally:
        db.close()

    assert status.status == "completed"
    assert status.progress == 100
    assert status.current_stage == "decision_summary"
    assert status.agents[-1].status == "completed"
    assert status.agents[-1].reasoning == "Additional review is required before a final decision."
