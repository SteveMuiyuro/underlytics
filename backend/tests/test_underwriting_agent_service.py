from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument
from underlytics_api.models.base import Base
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User
from underlytics_api.services.underwriting_agent_service import (
    build_autonomous_agent_input,
    execute_autonomous_underwriting_agent,
    get_agent_prompt_definition,
    prompt_registry_snapshot,
)


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_application(db: Session) -> Application:
    user = User(
        clerk_user_id="clerk-autonomous-user",
        role="applicant",
        email="autonomous@example.com",
        full_name="Autonomous Example",
    )
    product = LoanProduct(
        code="personal_autonomous",
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
        application_number="APP-AUTO-001",
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


def test_prompt_registry_contains_all_autonomous_underwriting_agents():
    snapshot = prompt_registry_snapshot()

    assert "document_analysis" in snapshot
    assert "policy_retrieval" in snapshot
    assert "risk_assessment" in snapshot
    assert "fraud_verification" in snapshot
    assert "decision_summary" in snapshot
    assert "email_agent" in snapshot
    assert snapshot["document_analysis"]["model_provider"] == "vertex_ai"
    assert snapshot["policy_retrieval"]["supports_mcp"] is True
    assert snapshot["decision_summary"]["model_name"] == "gpt-5.4"
    assert snapshot["decision_summary"]["fallback_model_names"] == ["gpt-5.3", "gpt-5.2"]
    assert snapshot["email_agent"]["model_provider"] == "vertex_ai"
    assert snapshot["email_agent"]["model_name"] == "gemini-2.5-flash"


def test_autonomous_agent_input_is_scoped_per_agent():
    db = make_session()

    try:
        application = seed_application(db)
        scoped_input = build_autonomous_agent_input(
            db,
            application=application,
            agent_name="risk_assessment",
            output_map={},
        )
    finally:
        db.close()

    assert "financials" in scoped_input
    assert "loan_product" not in scoped_input
    assert "uploaded_documents" not in scoped_input


def test_policy_and_fraud_agent_inputs_include_tool_evidence():
    db = make_session()

    try:
        application = seed_application(db)
        policy_input = build_autonomous_agent_input(
            db,
            application=application,
            agent_name="policy_retrieval",
            output_map={},
        )
        fraud_input = build_autonomous_agent_input(
            db,
            application=application,
            agent_name="fraud_verification",
            output_map={},
        )
    finally:
        db.close()

    assert policy_input["tool_evidence"][0]["tool_name"] == "policy_knowledgebase"
    assert fraud_input["tool_evidence"][0]["tool_name"] == "public_registry_lookup"


def test_autonomous_agent_execution_includes_prompt_metadata(monkeypatch):
    db = make_session()
    outputs = {
        "document_analysis": {
            "score": 0.9,
            "confidence": 0.95,
            "decision": "documents_complete",
            "flags": [],
            "reasoning": "All required documents are present.",
        },
        "policy_retrieval": {
            "score": 0.88,
            "confidence": 0.9,
            "decision": "policy_match",
            "flags": [],
            "reasoning": "Application fits loan product policy.",
        },
        "risk_assessment": {
            "score": 0.78,
            "confidence": 0.84,
            "decision": "low",
            "flags": [],
            "reasoning": "Income supports the requested term.",
        },
        "fraud_verification": {
            "score": 0.91,
            "confidence": 0.83,
            "decision": "clear",
            "flags": [],
            "reasoning": "No suspicious indicators detected.",
        },
        "decision_summary": {
            "score": 0.85,
            "confidence": 0.87,
            "decision": "approved",
            "flags": [],
            "reasoning": "All specialist checks support approval.",
        },
    }

    def fake_run_structured_agent(*, prompt, scoped_input, output_type):
        runtime_model_name = (
            "gpt-5.3" if prompt.agent_name == "decision_summary" else prompt.model_name
        )
        return {
            **outputs[prompt.agent_name],
            "__runtime": {
                "model_provider": prompt.model_provider,
                "model_name": runtime_model_name,
            },
        }

    monkeypatch.setattr(
        "underlytics_api.services.underwriting_agent_service._run_structured_agent",
        fake_run_structured_agent,
    )

    try:
        application = seed_application(db)
        document_execution = execute_autonomous_underwriting_agent(
            db,
            application=application,
            agent_name="document_analysis",
            output_map={},
        )
        policy_execution = execute_autonomous_underwriting_agent(
            db,
            application=application,
            agent_name="policy_retrieval",
            output_map={},
        )
        risk_execution = execute_autonomous_underwriting_agent(
            db,
            application=application,
            agent_name="risk_assessment",
            output_map={},
        )
        fraud_execution = execute_autonomous_underwriting_agent(
            db,
            application=application,
            agent_name="fraud_verification",
            output_map={},
        )
        decision_execution = execute_autonomous_underwriting_agent(
            db,
            application=application,
            agent_name="decision_summary",
            output_map={
                "document_analysis": document_execution.output,
                "policy_retrieval": policy_execution.output,
                "risk_assessment": risk_execution.output,
                "fraud_verification": fraud_execution.output,
            },
        )
    finally:
        db.close()

    assert document_execution.output["agent_metadata"]["agent_name"] == "document_analysis"
    assert document_execution.output["agent_metadata"]["prompt_version"] == "v2"
    assert document_execution.output["agent_metadata"]["model_provider"] == "vertex_ai"
    assert document_execution.output["agent_metadata"]["model_name"] == "gemini-2.5-flash"
    assert decision_execution.prompt.model_name == "gpt-5.4"
    assert decision_execution.output["agent_metadata"]["model_provider"] == "openai"
    assert decision_execution.output["agent_metadata"]["model_name"] == "gpt-5.3"
    assert decision_execution.output["agent_metadata"]["fallback_model_names"] == [
        "gpt-5.3",
        "gpt-5.2",
    ]
    assert decision_execution.output["decision"] in {"approved", "manual_review", "rejected"}


def test_get_agent_prompt_definition_returns_distinct_system_prompts():
    document_prompt = get_agent_prompt_definition("document_analysis")
    decision_prompt = get_agent_prompt_definition("decision_summary")
    email_prompt = get_agent_prompt_definition("email_agent")

    assert document_prompt.system_prompt != decision_prompt.system_prompt
    assert document_prompt.role == "Document Analysis Worker"
    assert decision_prompt.role == "Decision Summary Agent"
    assert email_prompt.model_provider == "vertex_ai"
    assert email_prompt.model_name == "gemini-2.5-flash"
