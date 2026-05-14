from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.models.application import Application
from underlytics_api.models.application_document import ApplicationDocument
from underlytics_api.models.base import Base
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.models.underwriting_job import UnderwritingJob
from underlytics_api.models.user import User
from underlytics_api.services.workflow_service import (
    create_underwriting_workflow,
    restart_underwriting_workflow,
)


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def seed_application(db: Session) -> Application:
    user = User(
        clerk_user_id="clerk-test-user",
        role="applicant",
        email="workflow@example.com",
        full_name="Workflow Example",
    )
    product = LoanProduct(
        code="salary_advance",
        name="Salary Advance",
        description="Short-term product",
        min_amount=500,
        max_amount=10000,
        min_term_months=1,
        max_term_months=6,
        is_active=True,
    )
    db.add(user)
    db.add(product)
    db.commit()
    db.refresh(user)
    db.refresh(product)

    application = Application(
        application_number="APP-WF-001",
        applicant_user_id=user.id,
        loan_product_id=product.id,
        status="submitted",
        requested_amount=3000,
        requested_term_months=3,
        monthly_income=3500,
        monthly_expenses=700,
        existing_loan_obligations=100,
        employment_status="full_time",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    for document_type in ("id_document", "payslip", "bank_statement"):
        db.add(
            ApplicationDocument(
                application_id=application.id,
                document_type=document_type,
                file_name=f"{document_type}.pdf",
                file_path=f"/tmp/{document_type}.pdf",
                mime_type="application/pdf",
                file_size_bytes=1024,
                upload_status="uploaded",
                is_required=True,
            )
        )

    db.commit()
    db.refresh(application)
    return application


def test_create_underwriting_workflow_completes_for_low_risk_application():
    db = make_session()

    try:
        application = seed_application(db)
        job = create_underwriting_workflow(db, application.id)
        db.refresh(application)
    finally:
        db.close()

    assert job.status == "completed"
    assert application.status == "approved"


def test_create_underwriting_workflow_reuses_existing_active_job(monkeypatch):
    db = make_session()

    try:
        application = seed_application(db)
        existing_job = UnderwritingJob(
            application_id=application.id,
            status="running",
            current_step="risk_assessment",
        )
        db.add(existing_job)
        db.commit()
        db.refresh(existing_job)

        monkeypatch.setattr(
            "underlytics_api.services.workflow_service.materialize_underwriting_plan",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("Should not create a new workflow plan")
            ),
        )

        job = create_underwriting_workflow(db, application.id)
    finally:
        db.close()

    assert job.id == existing_job.id


def test_create_underwriting_workflow_reuses_existing_completed_job_for_final_application(
    monkeypatch,
):
    db = make_session()

    try:
        application = seed_application(db)
        application.status = "approved"
        db.add(application)
        db.commit()

        existing_job = UnderwritingJob(
            application_id=application.id,
            status="completed",
            current_step="workers_completed",
        )
        db.add(existing_job)
        db.commit()
        db.refresh(existing_job)

        monkeypatch.setattr(
            "underlytics_api.services.workflow_service.materialize_underwriting_plan",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                AssertionError("Should not create a new workflow plan")
            ),
        )

        job = create_underwriting_workflow(db, application.id)
    finally:
        db.close()

    assert job.id == existing_job.id


def test_restart_underwriting_workflow_forces_new_run(monkeypatch):
    db = make_session()
    observed: dict = {}

    try:
        application = seed_application(db)
        application.status = "approved"
        db.add(application)
        db.commit()

        existing_job = UnderwritingJob(
            application_id=application.id,
            status="completed",
            current_step="workers_completed",
        )
        db.add(existing_job)
        db.commit()

        monkeypatch.setattr(
            "underlytics_api.services.workflow_service.materialize_underwriting_plan",
            lambda *args, **kwargs: "fake-plan",
        )

        def fake_run_workflow_plan(db, plan):
            observed["plan"] = plan
            return UnderwritingJob(application_id=application.id, status="completed")

        monkeypatch.setattr(
            "underlytics_api.services.workflow_service.run_workflow_plan",
            fake_run_workflow_plan,
        )

        job = restart_underwriting_workflow(db, application.id)
    finally:
        db.close()

    assert observed["plan"] == "fake-plan"
    assert job.application_id == application.id
