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

    def send_email(self, *, to_email: str, subject: str, body_text: str):
        self.sent.append((to_email, subject, body_text))
        return notification_service.EmailDeliveryResult(
            provider_name=self.provider_name,
            provider_message_id="msg_test_123",
        )


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_application(db: Session) -> Application:
    user = User(
        clerk_user_id="clerk-email-user",
        role="applicant",
        email="applicant@example.com",
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


def test_send_automated_decision_notification_creates_sent_log(monkeypatch):
    db = make_session()
    provider = FakeProvider()
    monkeypatch.setattr(notification_service, "_get_email_provider", lambda: provider)

    try:
        application = seed_application(db)
        db.add(
            AgentOutput(
                agent_run_id="run-1",
                application_id=application.id,
                agent_name="decision_summary",
                score=0.9,
                confidence=0.88,
                decision="approved",
                flags="[]",
                reasoning="Application meets underwriting thresholds.",
                output_json="{}",
            )
        )
        db.commit()

        log = notification_service.send_automated_decision_notification(
            db,
            application_id=application.id,
            decision="approved",
        )
    finally:
        db.close()

    assert log is not None
    assert log.status == "sent"
    assert log.provider_name == "fake"
    assert provider.sent[0][0] == "applicant@example.com"
    assert "Approved" in provider.sent[0][1]


def test_send_manual_review_completed_notification_uses_reviewer_note(monkeypatch):
    db = make_session()
    provider = FakeProvider()
    monkeypatch.setattr(notification_service, "_get_email_provider", lambda: provider)

    try:
        application = seed_application(db)
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
            status="resolved",
            reason="Escalated for review",
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        db.add(
            AgentOutput(
                agent_run_id="run-2",
                application_id=application.id,
                agent_name="decision_summary",
                score=0.55,
                confidence=0.8,
                decision="approved",
                flags='["manual_review"]',
                reasoning="Reviewer approval confirmed the application.",
                output_json="{}",
            )
        )
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
        stored_logs = db.query(CommunicationLog).all()
    finally:
        db.close()

    assert log is not None
    assert log.status == "sent"
    assert len(stored_logs) == 1
    assert "Manual review completed" in log.subject
    assert "Approved after confirming supporting bank statements." in provider.sent[0][2]
