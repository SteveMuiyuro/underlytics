import json
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.models.agent_evaluation import AgentEvaluation
from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument
from underlytics_api.models.base import Base
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User
from underlytics_api.services.orchestrator_service import materialize_underwriting_plan
from underlytics_api.services.worker_service import run_workflow_plan


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_application(db: Session) -> Application:
    user = User(
        clerk_user_id="clerk-worker-user",
        role="applicant",
        email="worker@example.com",
        full_name="Worker Example",
    )
    product = LoanProduct(
        code="personal_worker",
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
        application_number="APP-WORKER-001",
        applicant_user_id=user.id,
        loan_product_id=product.id,
        status="submitted",
        requested_amount=5000,
        requested_term_months=12,
        monthly_income=3000,
        monthly_expenses=900,
        existing_loan_obligations=250,
        employment_status="Employed",
        employer_name="Acme Ltd",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    db.add_all(
        [
            ApplicationDocument(
                application_id=application.id,
                document_type="id_document",
                file_name="id.pdf",
                file_path="/tmp/id.pdf",
                mime_type="application/pdf",
                file_size_bytes=1200,
                upload_status="uploaded",
                is_required=True,
            ),
            ApplicationDocument(
                application_id=application.id,
                document_type="payslip",
                file_name="payslip.pdf",
                file_path="/tmp/payslip.pdf",
                mime_type="application/pdf",
                file_size_bytes=1200,
                upload_status="uploaded",
                is_required=True,
            ),
            ApplicationDocument(
                application_id=application.id,
                document_type="bank_statement",
                file_name="statement.pdf",
                file_path="/tmp/statement.pdf",
                mime_type="application/pdf",
                file_size_bytes=1200,
                upload_status="uploaded",
                is_required=True,
            ),
        ]
    )
    db.commit()
    return application


def test_run_workflow_plan_records_agent_evaluations(monkeypatch):
    db = make_session()
    observed_guardrail: dict = {}

    def fake_planner_run(*, prompt, scoped_input, output_type):
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

    outputs = {
        "document_analysis": {
            "score": 0.9,
            "confidence": 0.95,
            "decision": "documents_complete",
            "flags": [],
            "reasoning": "All required documents are present.",
            "agent_metadata": {},
        },
        "policy_retrieval": {
            "score": 0.88,
            "confidence": 0.9,
            "decision": "policy_match",
            "flags": [],
            "reasoning": "Application fits policy.",
            "agent_metadata": {},
        },
        "risk_assessment": {
            "score": 0.52,
            "confidence": 0.84,
            "decision": "medium",
            "flags": ["elevated_dti"],
            "reasoning": "Disposable income is tighter than preferred.",
            "agent_metadata": {},
        },
        "fraud_verification": {
            "score": 0.91,
            "confidence": 0.83,
            "decision": "clear",
            "flags": [],
            "reasoning": "No suspicious indicators detected.",
            "agent_metadata": {},
        },
        "decision_summary": {
            "score": 0.85,
            "confidence": 0.87,
            "decision": "approved",
            "flags": [],
            "reasoning": "All specialist checks support approval.",
            "agent_metadata": {},
        },
    }

    class FakeExecution:
        def __init__(self, agent_name: str):
            self.output = outputs[agent_name]
            self.prompt = type(
                "Prompt",
                (),
                {
                    "agent_name": agent_name,
                    "role": agent_name,
                    "model_provider": "vertex_ai"
                    if agent_name != "decision_summary"
                    else "openai",
                    "model_name": "gemini-2.5-flash"
                    if agent_name != "decision_summary"
                    else "gpt-5.4",
                    "prompt_version": "v2",
                    "supports_mcp": agent_name in {"policy_retrieval", "fraud_verification"},
                    "allowed_tools": (
                        ("policy_knowledgebase",)
                        if agent_name == "policy_retrieval"
                        else ("public_registry_lookup",)
                        if agent_name == "fraud_verification"
                        else ()
                    ),
                },
            )()
            tool_evidence = []
            if agent_name == "policy_retrieval":
                tool_evidence = [
                    {
                        "tool_name": "policy_knowledgebase",
                        "status": "completed",
                        "source": "internal_policy_catalog",
                    }
                ]
            if agent_name == "fraud_verification":
                tool_evidence = [
                    {
                        "tool_name": "public_registry_lookup",
                        "status": "completed",
                        "source": "fixture_public_registry",
                    }
                ]
            self.scoped_input = {"input": {"tool_evidence": tool_evidence}}
            self.execution_mode = "autonomous_llm"

    @contextmanager
    def fake_start_guardrail_observability(*, trace_core, name, metadata):
        observed_guardrail["trace_core"] = trace_core
        observed_guardrail["name"] = name
        observed_guardrail["metadata"] = metadata

        class Observation:
            def record_output(self, *, output=None, metadata=None, status_message=None):
                observed_guardrail["output"] = output
                observed_guardrail["output_metadata"] = metadata

            def record_error(self, *, message, data=None):
                observed_guardrail["error"] = (message, data)

        yield Observation()

    monkeypatch.setattr(
        "underlytics_api.services.planner_service._run_structured_agent",
        fake_planner_run,
    )
    monkeypatch.setattr(
        "underlytics_api.services.worker_service.execute_autonomous_underwriting_agent",
        lambda db, application, agent_name, output_map: FakeExecution(agent_name),
    )
    monkeypatch.setattr(
        "underlytics_api.services.worker_service.send_automated_decision_notification",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "underlytics_api.services.worker_service.send_manual_review_escalation_notification",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "underlytics_api.services.worker_service.start_guardrail_observability",
        fake_start_guardrail_observability,
    )

    try:
        application = seed_application(db)
        plan = materialize_underwriting_plan(db, application.id)
        run_workflow_plan(db, plan)
        evaluations = (
            db.query(AgentEvaluation)
            .order_by(AgentEvaluation.agent_name.asc())
            .all()
        )
    finally:
        db.close()

    assert len(evaluations) == 5
    decision_summary_eval = next(
        evaluation for evaluation in evaluations if evaluation.agent_name == "decision_summary"
    )
    assert decision_summary_eval.decision == "approved"
    assert decision_summary_eval.final_decision == "manual_review"
    assert decision_summary_eval.guardrail_adjusted is True
    policy_eval = next(
        evaluation for evaluation in evaluations if evaluation.agent_name == "policy_retrieval"
    )
    fraud_eval = next(
        evaluation for evaluation in evaluations if evaluation.agent_name == "fraud_verification"
    )
    assert policy_eval.tool_evidence_count == 1
    assert fraud_eval.tool_evidence_count == 1
    assert json.loads(policy_eval.evaluation_json)["tool_sources"] == [
        "internal_policy_catalog"
    ]
    assert observed_guardrail["name"] == "decision_summary_guardrails"
    assert observed_guardrail["metadata"]["proposed_decision"] == "approved"
    assert observed_guardrail["output"]["final_decision"] == "manual_review"
