from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.api.applications import create_application, get_application_evaluations
from underlytics_api.core.auth import ActorContext
from underlytics_api.models.agent_evaluation import AgentEvaluation
from underlytics_api.models.application import Application
from underlytics_api.models.base import Base
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User
from underlytics_api.schemas.application import ApplicationCreate


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_application_with_evaluation(db: Session) -> Application:
    user = User(
        clerk_user_id="clerk-api-user",
        role="applicant",
        email="api@example.com",
        full_name="API Example",
    )
    product = LoanProduct(
        code="api_product",
        name="API Product",
        description="API Product",
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
        application_number="APP-API-001",
        applicant_user_id=user.id,
        loan_product_id=product.id,
        status="manual_review",
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
        AgentEvaluation(
            workflow_step_attempt_id="attempt-1",
            workflow_step_id="step-1",
            application_id=application.id,
            agent_name="decision_summary",
            status="completed",
            schema_valid=True,
            guardrail_adjusted=True,
            decision="approved",
            final_decision="manual_review",
            tool_evidence_count=0,
            completed_tool_evidence_count=0,
            latency_ms=1250,
            model_provider="openai",
            model_name="gpt-5.4",
            prompt_version="v2",
            evaluation_json="{}",
            created_at=datetime.utcnow(),
        )
    )
    db.commit()
    return application


def seed_user_and_product(db: Session) -> tuple[User, LoanProduct]:
    user = User(
        clerk_user_id="clerk-create-user",
        role="applicant",
        email="create@example.com",
        full_name="Create Example",
    )
    product = LoanProduct(
        code="create_product",
        name="Create Product",
        description="Create Product",
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
    return user, product


def test_get_application_evaluations_returns_flat_list():
    db = make_session()
    application = seed_application_with_evaluation(db)
    actor = ActorContext(
        clerk_user_id="clerk-api-user",
        backend_user_id=application.applicant_user_id,
        role="applicant",
        token_verified=True,
    )

    try:
        payload = get_application_evaluations(
            application_number=application.application_number,
            db=db,
            actor=actor,
        )
    finally:
        db.close()

    assert len(payload) == 1
    assert payload[0].agent_name == "decision_summary"
    assert payload[0].decision == "approved"
    assert payload[0].final_decision == "manual_review"
    assert payload[0].guardrail_adjusted is True


def test_create_application_clears_hidden_optional_fields():
    db = make_session()
    user, product = seed_user_and_product(db)
    actor = ActorContext(
        clerk_user_id=user.clerk_user_id,
        backend_user_id=user.id,
        role="applicant",
        token_verified=True,
    )

    try:
        application = create_application(
            payload=ApplicationCreate(
                applicant_user_id=user.id,
                loan_product_id=product.id,
                requested_amount=5000,
                requested_term_months=12,
                loan_purpose="Working capital",
                monthly_income=3000,
                monthly_expenses=900,
                existing_loan_obligations=0,
                employment_status="self_employed",
                employer_name="Should Be Cleared",
                bank_name="Should Also Clear",
                account_type="business",
                auto_start_workflow=False,
            ),
            db=db,
            actor=actor,
        )
    finally:
        db.close()

    assert application.employment_status == "self_employed"
    assert application.existing_loan_obligations == 0
    assert application.employer_name is None
    assert application.bank_name is None
    assert application.account_type is None
