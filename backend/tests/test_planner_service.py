from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument
from underlytics_api.models.base import Base
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User
from underlytics_api.services.planner_service import build_underwriting_plan


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_application(db: Session) -> Application:
    user = User(
        clerk_user_id="clerk-planner-user",
        role="applicant",
        email="planner@example.com",
        full_name="Planner Example",
    )
    product = LoanProduct(
        code="personal_planner",
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
        application_number="APP-PLANNER-001",
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

    db.add(
        ApplicationDocument(
            application_id=application.id,
            document_type="id_document",
            file_name="id.pdf",
            file_path="/tmp/id.pdf",
            mime_type="application/pdf",
            file_size_bytes=1200,
            upload_status="uploaded",
            is_required=True,
        )
    )
    db.commit()
    return application


def test_build_underwriting_plan_uses_agent_output(monkeypatch):
    db = make_session()
    observed: dict = {}

    def fake_run_structured_agent(*, prompt, scoped_input, output_type):
        return {
            "plan_version": "v1",
            "planner_mode": "agentic_vertex",
            "summary": "Planner created an agentic underwriting workflow.",
            "metadata": {"planner_source": "llm"},
            "steps": [
                {
                    "step_key": "document_analysis",
                    "step_type": "worker",
                    "worker_name": "document_analysis",
                    "queue_name": "underwriting",
                    "priority": 10,
                    "dependencies": [],
                    "input_context": {},
                },
                {
                    "step_key": "policy_retrieval",
                    "step_type": "worker",
                    "worker_name": "policy_retrieval",
                    "queue_name": "underwriting",
                    "priority": 20,
                    "dependencies": [],
                    "input_context": {},
                },
                {
                    "step_key": "risk_assessment",
                    "step_type": "worker",
                    "worker_name": "risk_assessment",
                    "queue_name": "underwriting",
                    "priority": 30,
                    "dependencies": [],
                    "input_context": {},
                },
                {
                    "step_key": "fraud_verification",
                    "step_type": "worker",
                    "worker_name": "fraud_verification",
                    "queue_name": "underwriting",
                    "priority": 40,
                    "dependencies": [],
                    "input_context": {},
                },
                {
                    "step_key": "decision_summary",
                    "step_type": "worker",
                    "worker_name": "decision_summary",
                    "queue_name": "underwriting",
                    "priority": 50,
                    "dependencies": [
                        "document_analysis",
                        "policy_retrieval",
                        "risk_assessment",
                        "fraud_verification",
                    ],
                    "input_context": {},
                },
            ],
        }

    @contextmanager
    def fake_start_agent_observability(
        *,
        trace_name,
        trace_context,
        metadata,
        input_payload,
        observation_type="agent",
    ):
        observed["trace_name"] = trace_name
        observed["trace_context"] = trace_context
        observed["metadata"] = metadata
        observed["input_payload"] = input_payload
        observed["observation_type"] = observation_type

        class Observation:
            def record_output(self, *, output=None, metadata=None, status_message=None):
                observed["output"] = output
                observed["output_metadata"] = metadata

            def record_error(self, *, message, data=None):
                observed["error"] = (message, data)

        yield Observation()

    monkeypatch.setattr(
        "underlytics_api.services.planner_service._run_structured_agent",
        fake_run_structured_agent,
    )
    monkeypatch.setattr(
        "underlytics_api.services.planner_service.ensure_trace_context",
        lambda **kwargs: "planner-trace-context",
    )
    monkeypatch.setattr(
        "underlytics_api.services.planner_service.start_agent_observability",
        fake_start_agent_observability,
    )

    try:
        application = seed_application(db)
        plan = build_underwriting_plan(db, application)
    finally:
        db.close()

    assert plan.planner_mode == "agentic_vertex"
    assert len(plan.steps) == 5
    assert plan.metadata["planner_source"] == "llm"
    assert plan.metadata["planner_agent"]["model_provider"] == "vertex_ai"
    assert observed["trace_name"] == "underlytics-planner-agent"
    assert observed["trace_context"] == "planner-trace-context"
    assert observed["metadata"]["agent_name"] == "planner"
    assert observed["input_payload"]["application"]["application_number"] == "APP-PLANNER-001"
    assert observed["output"]["planner_mode"] == "agentic_vertex"
