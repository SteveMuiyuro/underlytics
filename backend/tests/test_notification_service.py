from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.models.agent_output import AgentOutput
from underlytics_api.models.application import Application
from underlytics_api.models.base import Base
from underlytics_api.models.communication_log import CommunicationLog
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.manual_review_action import ManualReviewAction
from underlytics_api.models.manual_review_case import ManualReviewCase
from underlytics_api.models.user import User
from underlytics_api.models.workflow_plan import WorkflowPlan
from underlytics_api.services import notification_service


class FakeProvider:
    provider_name = "fake"

    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []

    def send_email(self, *, to_email: str, subject: str, html_body: str):
        self.sent.append((to_email, subject, html_body))
        return notification_service.EmailDeliveryResult(
            provider_name=self.provider_name,
            provider_message_id="msg_test_123",
        )


class FailingProvider:
    provider_name = "fake"

    def send_email(self, *, to_email: str, subject: str, html_body: str):
        raise RuntimeError("provider down")


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_application(db: Session, *, email: str = "applicant@example.com") -> Application:
    user = User(
        clerk_user_id="clerk-email-user",
        role="applicant",
        email=email,
        full_name="Applicant Example",
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
        application_number="APP-NOTIFY-001",
        applicant_user_id=user.id,
        loan_product_id=product.id,
        status="approved",
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


def add_decision_output(
    db: Session,
    *,
    application_id: str,
    decision: str,
    reasoning: str,
    flags: str = "[]",
) -> None:
    db.add(
        AgentOutput(
            agent_run_id=f"run-{decision}",
            application_id=application_id,
            agent_name="decision_summary",
            score=0.9,
            confidence=0.88,
            decision=decision,
            flags=flags,
            reasoning=reasoning,
            output_json="{}",
        )
    )
    db.commit()


def create_manual_review_case(db: Session, *, application: Application) -> ManualReviewCase:
    plan = WorkflowPlan(
        application_id=application.id,
        plan_version="v1",
        planner_mode="deterministic_foundation",
        status="awaiting_review",
        summary="Manual review required",
        plan_json="{}",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    case = ManualReviewCase(
        application_id=application.id,
        workflow_plan_id=plan.id,
        status="open",
        reason="Escalated for review",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_generate_application_email_returns_html_for_all_email_types(monkeypatch):
    db = make_session()

    try:
        application = seed_application(db)
        add_decision_output(
            db,
            application_id=application.id,
            decision="approved",
            reasoning="Application meets underwriting thresholds.",
        )
        context = notification_service._load_application_email_context(
            db,
            application_id=application.id,
        )

        def fake_run_structured_agent(*, prompt, scoped_input, output_type):
            return {
                "subject": f"{scoped_input['email_type']} subject",
                "html_body": "<!doctype html><html><body>Email</body></html>",
            }

        monkeypatch.setattr(
            notification_service,
            "_run_structured_agent",
            fake_run_structured_agent,
        )
        for email_type in sorted(notification_service.EMAIL_TYPES):
            payload = notification_service.generate_application_email(
                application=context.application,
                agent_outputs=context.agent_outputs,
                email_type=email_type,
                reviewer_note="Approved after confirming supporting bank statements.",
                reviewer_decision="approved",
            )
            assert payload["subject"]
            assert payload["html_body"].startswith("<!doctype html>")
    finally:
        db.close()


def test_generate_application_email_records_email_agent_trace(monkeypatch):
    db = make_session()
    observed: dict = {}

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
        notification_service,
        "ensure_trace_context",
        lambda **kwargs: "email-trace-context",
    )
    monkeypatch.setattr(
        notification_service,
        "start_agent_observability",
        fake_start_agent_observability,
    )
    monkeypatch.setattr(
        notification_service,
        "_run_structured_agent",
        lambda **kwargs: {
            "subject": "Approved",
            "html_body": "<!doctype html><html><body>Approved</body></html>",
        },
    )

    try:
        application = seed_application(db)
        add_decision_output(
            db,
            application_id=application.id,
            decision="approved",
            reasoning="Application meets underwriting thresholds.",
        )
        context = notification_service._load_application_email_context(
            db,
            application_id=application.id,
        )
        payload = notification_service.generate_application_email(
            application=context.application,
            agent_outputs=context.agent_outputs,
            email_type="agent_final_approved",
        )
    finally:
        db.close()

    assert payload["subject"] == "Approved"
    assert observed["trace_name"] == "underlytics-email-agent"
    assert observed["trace_context"] == "email-trace-context"
    assert observed["metadata"]["email_type"] == "agent_final_approved"
    assert observed["metadata"]["model_provider"] == "vertex_ai"
    assert observed["metadata"]["model_name"] == "gemini-2.5-flash"
    assert observed["input_payload"]["application"]["application_number"] == "APP-NOTIFY-001"
    assert observed["output"]["subject"] == "Approved"


def test_send_automated_decision_notification_creates_sent_log(monkeypatch):
    db = make_session()
    provider = FakeProvider()
    monkeypatch.setattr(notification_service, "_build_email_provider", lambda: provider)
    monkeypatch.setattr(
        notification_service,
        "_run_structured_agent",
        lambda **kwargs: {
            "subject": "Approved",
            "html_body": "<!doctype html><html><body>Approved</body></html>",
        },
    )

    try:
        application = seed_application(db)
        add_decision_output(
            db,
            application_id=application.id,
            decision="approved",
            reasoning="Application meets underwriting thresholds.",
        )

        log = notification_service.send_automated_decision_notification(
            db,
            application_id=application.id,
            decision="approved",
        )
    finally:
        db.close()

    assert log is not None
    assert log.status == "sent"
    assert log.template_key == "agent_final_approved"
    assert log.recipient_email == "applicant@example.com"
    assert provider.sent[0][0] == "applicant@example.com"
    assert "<html>" in provider.sent[0][2]


def test_load_application_email_context_uses_applicant_user_email():
    db = make_session()

    try:
        application = seed_application(db, email="resolved@example.com")
        context = notification_service._load_application_email_context(
            db,
            application_id=application.id,
        )
    finally:
        db.close()

    assert context.applicant.email == "resolved@example.com"


def test_send_automated_rejected_notification_uses_applicant_email(monkeypatch):
    db = make_session()
    provider = FakeProvider()
    monkeypatch.setattr(notification_service, "_build_email_provider", lambda: provider)
    monkeypatch.setattr(
        notification_service,
        "_run_structured_agent",
        lambda **kwargs: {
            "subject": "Rejected",
            "html_body": "<!doctype html><html><body>Rejected</body></html>",
        },
    )

    try:
        application = seed_application(db, email="rejected@example.com")
        application.status = "rejected"
        db.add(application)
        db.commit()
        add_decision_output(
            db,
            application_id=application.id,
            decision="rejected",
            reasoning="Application does not meet underwriting thresholds.",
        )

        log = notification_service.send_automated_decision_notification(
            db,
            application_id=application.id,
            decision="rejected",
        )
    finally:
        db.close()

    assert log is not None
    assert log.status == "sent"
    assert log.template_key == "agent_final_rejected"
    assert log.recipient_email == "rejected@example.com"
    assert provider.sent[0][0] == "rejected@example.com"


def test_send_manual_review_escalation_notification_is_deduplicated(monkeypatch):
    db = make_session()
    provider = FakeProvider()
    monkeypatch.setattr(notification_service, "_build_email_provider", lambda: provider)
    monkeypatch.setattr(
        notification_service,
        "_run_structured_agent",
        lambda **kwargs: {
            "subject": "Manual review",
            "html_body": "<!doctype html><html><body>Manual review</body></html>",
        },
    )

    try:
        application = seed_application(db)
        application.status = "manual_review"
        db.add(application)
        db.commit()
        add_decision_output(
            db,
            application_id=application.id,
            decision="manual_review",
            reasoning="Additional review is required before a final decision.",
        )
        case = create_manual_review_case(db, application=application)

        first_log = notification_service.send_manual_review_escalation_notification(
            db,
            manual_review_case_id=case.id,
        )
        second_log = notification_service.send_manual_review_escalation_notification(
            db,
            manual_review_case_id=case.id,
        )
        stored_logs = db.query(CommunicationLog).all()
    finally:
        db.close()

    assert first_log is not None
    assert first_log.template_key == "manual_review_escalated"
    assert second_log is None
    assert len(stored_logs) == 1


def test_send_manual_review_completed_notification_uses_final_email_type(monkeypatch):
    db = make_session()
    provider = FakeProvider()
    monkeypatch.setattr(notification_service, "_build_email_provider", lambda: provider)
    monkeypatch.setattr(
        notification_service,
        "_run_structured_agent",
        lambda **kwargs: {
            "subject": "Application approved",
            "html_body": "<!doctype html><html><body>Application approved</body></html>",
        },
    )

    try:
        application = seed_application(db)
        application.status = "approved"
        db.add(application)
        db.commit()
        add_decision_output(
            db,
            application_id=application.id,
            decision="approved",
            reasoning="A reviewer confirmed the application can move forward.",
        )
        case = create_manual_review_case(db, application=application)
        case.status = "resolved"
        db.add(case)
        db.commit()

        db.add(
            ManualReviewAction(
                manual_review_case_id=case.id,
                reviewer_user_id=application.applicant_user_id,
                action="approve",
                note="Approved after confirming supporting bank statements.",
                old_decision="manual_review",
                new_decision="approved",
            )
        )
        db.commit()

        log = notification_service.send_manual_review_completed_notification(
            db,
            manual_review_case_id=case.id,
        )
    finally:
        db.close()

    assert log is not None
    assert log.status == "sent"
    assert log.template_key == "manual_review_final_approved"
    assert log.recipient_email == "applicant@example.com"
    assert provider.sent[0][0] == "applicant@example.com"
    assert "Application approved" in provider.sent[0][2]


def test_send_application_email_skips_when_recipient_is_missing():
    db = make_session()

    try:
        application = seed_application(db, email="")
        log = notification_service.send_application_email(
            db=db,
            application_id=application.id,
            to_email="",
            subject="Subject",
            html_body="<!doctype html><html><body>Body</body></html>",
            email_type="agent_final_rejected",
        )
    finally:
        db.close()

    assert log.status == "skipped"
    assert log.error_message == "Recipient email is missing"


def test_send_automated_decision_notification_skips_when_applicant_email_missing(
    monkeypatch,
):
    db = make_session()
    provider = FakeProvider()
    monkeypatch.setattr(notification_service, "_build_email_provider", lambda: provider)
    monkeypatch.setattr(
        notification_service,
        "_run_structured_agent",
        lambda **kwargs: {
            "subject": "Approved",
            "html_body": "<!doctype html><html><body>Approved</body></html>",
        },
    )

    try:
        application = seed_application(db, email="")
        add_decision_output(
            db,
            application_id=application.id,
            decision="approved",
            reasoning="Application meets underwriting thresholds.",
        )

        log = notification_service.send_automated_decision_notification(
            db,
            application_id=application.id,
            decision="approved",
        )
    finally:
        db.close()

    assert log is not None
    assert log.status == "skipped"
    assert log.recipient_email == ""
    assert log.error_message == "Recipient email is missing"
    assert provider.sent == []


def test_send_application_email_marks_failed_provider_attempt(monkeypatch):
    db = make_session()
    monkeypatch.setattr(
        notification_service,
        "_build_email_provider",
        lambda: FailingProvider(),
    )

    try:
        application = seed_application(db)
        log = notification_service.send_application_email(
            db=db,
            application_id=application.id,
            to_email="applicant@example.com",
            subject="Subject",
            html_body="<!doctype html><html><body>Body</body></html>",
            email_type="agent_final_rejected",
        )
    finally:
        db.close()

    assert log.status == "failed"
    assert log.error_message == "Email delivery failed: RuntimeError"
