from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.models.application import Application
from underlytics_api.models.base import Base
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.user import User
from underlytics_api.services.mcp_evidence_service import build_mcp_tool_evidence


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_application(
    db: Session,
    *,
    employer_name: str = "Acme Ltd",
    product_code: str = "salary_advance",
) -> Application:
    user = User(
        clerk_user_id="clerk-mcp-user",
        role="applicant",
        email="applicant@example.com",
        full_name="Applicant Example",
        phone_number="+254700000001",
    )
    product = LoanProduct(
        code=product_code,
        name="Seed Product",
        description="Seed Product",
        min_amount=500,
        max_amount=10000,
        min_term_months=1,
        max_term_months=6,
        is_active=True,
    )
    db.add_all([user, product])
    db.commit()
    db.refresh(user)
    db.refresh(product)

    application = Application(
        application_number="APP-MCP-001",
        applicant_user_id=user.id,
        loan_product_id=product.id,
        status="submitted",
        requested_amount=3000,
        requested_term_months=3,
        monthly_income=3000,
        monthly_expenses=900,
        existing_loan_obligations=100,
        employment_status="Employed",
        employer_name=employer_name,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def test_policy_retrieval_mcp_evidence_uses_internal_policy_catalog():
    db = make_session()

    try:
        application = seed_application(db)
        evidence = build_mcp_tool_evidence(
            db,
            application=application,
            agent_name="policy_retrieval",
        )
    finally:
        db.close()

    assert evidence[0]["tool_name"] == "policy_knowledgebase"
    assert evidence[0]["source"] == "internal_policy_catalog"
    assert evidence[0]["cost_tier"] == "free"
    assert evidence[0]["evidence"]["computed_checks"]["amount_within_range"] is True


def test_fraud_verification_mcp_evidence_uses_fixture_public_registry():
    db = make_session()

    try:
        application = seed_application(db, employer_name="Acme Ltd")
        evidence = build_mcp_tool_evidence(
            db,
            application=application,
            agent_name="fraud_verification",
        )
    finally:
        db.close()

    assert evidence[0]["tool_name"] == "public_registry_lookup"
    assert evidence[0]["source"] == "fixture_public_registry"
    assert evidence[0]["evidence"]["match_found"] is True
    assert evidence[0]["evidence"]["registered_name"] == "Acme Ltd"
