from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.models.application import Application
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
        clerk_user_id="clerk-test-user",
        role="applicant",
        email="applicant@example.com",
        full_name="Applicant Example",
    )
    product = LoanProduct(
        code="personal",
        name="Personal Loan",
        description="Personal financing",
        min_amount=1000,
        max_amount=50000,
        min_term_months=3,
        max_term_months=24,
        is_active=True,
    )
    db.add(user)
    db.add(product)
    db.commit()
    db.refresh(user)
    db.refresh(product)

    application = Application(
        application_number="APP-TEST-001",
        applicant_user_id=user.id,
        loan_product_id=product.id,
        status="submitted",
        requested_amount=4000,
        requested_term_months=12,
        monthly_income=3000,
        monthly_expenses=1000,
        existing_loan_obligations=200,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def test_planner_marks_missing_documents_in_metadata():
    db = make_session()

    try:
        application = seed_application(db)
        plan = build_underwriting_plan(db, application)
    finally:
        db.close()

    assert plan.planner_mode == "deterministic_foundation"
    assert sorted(plan.metadata["missing_required_document_types"]) == [
        "bank_statement",
        "id_document",
        "payslip",
    ]
    assert [step.step_key for step in plan.steps] == [
        "document_analysis",
        "policy_retrieval",
        "risk_assessment",
        "fraud_verification",
        "decision_summary",
    ]
