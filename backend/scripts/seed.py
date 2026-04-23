from sqlalchemy.orm import Session

from underlytics_api.db.database import SessionLocal, engine
from underlytics_api.models import Application, LoanProduct, User
from underlytics_api.models.base import Base


def seed_users(db: Session) -> None:
    users = [
        {
            "clerk_user_id": "clerk_applicant_001",
            "role": "applicant",
            "email": "john@example.com",
            "full_name": "John Doe",
            "phone_number": "+254700000001",
        },
        {
            "clerk_user_id": "clerk_applicant_002",
            "role": "applicant",
            "email": "jane@example.com",
            "full_name": "Jane Smith",
            "phone_number": "+254700000002",
        },
        {
            "clerk_user_id": "clerk_reviewer_001",
            "role": "reviewer",
            "email": "reviewer@underlytics.com",
            "full_name": "Grace Reviewer",
            "phone_number": "+254700000099",
        },
    ]

    for user_data in users:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            db.add(User(**user_data))

    db.commit()


def seed_loan_products(db: Session) -> None:
    loan_products = [
        {
            "code": "personal_loan",
            "name": "Personal Loan",
            "description": "General purpose personal financing product",
            "min_amount": 1000,
            "max_amount": 50000,
            "min_term_months": 3,
            "max_term_months": 24,
            "is_active": True,
        },
        {
            "code": "salary_advance",
            "name": "Salary Advance",
            "description": "Short term salary-backed loan product",
            "min_amount": 500,
            "max_amount": 10000,
            "min_term_months": 1,
            "max_term_months": 6,
            "is_active": True,
        },
        {
            "code": "small_business_loan",
            "name": "Small Business Loan",
            "description": "Working capital loan for small businesses",
            "min_amount": 5000,
            "max_amount": 100000,
            "min_term_months": 6,
            "max_term_months": 36,
            "is_active": True,
        },
    ]

    for product_data in loan_products:
        existing_product = (
            db.query(LoanProduct).filter(LoanProduct.code == product_data["code"]).first()
        )
        if not existing_product:
            db.add(LoanProduct(**product_data))

    db.commit()


def seed_applications(db: Session) -> None:
    john = db.query(User).filter(User.email == "john@example.com").first()
    jane = db.query(User).filter(User.email == "jane@example.com").first()

    personal_loan = db.query(LoanProduct).filter(LoanProduct.code == "personal_loan").first()
    salary_advance = db.query(LoanProduct).filter(LoanProduct.code == "salary_advance").first()
    small_business_loan = (
        db.query(LoanProduct).filter(LoanProduct.code == "small_business_loan").first()
    )

    applications = [
        {
            "application_number": "APP-001",
            "applicant_user_id": john.id,
            "loan_product_id": personal_loan.id,
            "status": "in_progress",
            "requested_amount": 5000,
            "requested_term_months": 12,
            "loan_purpose": "Emergency household expenses",
            "monthly_income": 2400,
            "monthly_expenses": 950,
            "existing_loan_obligations": 200,
            "employment_status": "Employed",
            "employer_name": "Acme Ltd",
            "bank_name": "Equity Bank",
            "account_type": "Savings",
        },
        {
            "application_number": "APP-002",
            "applicant_user_id": jane.id,
            "loan_product_id": salary_advance.id,
            "status": "approved",
            "requested_amount": 3000,
            "requested_term_months": 3,
            "loan_purpose": "Short term cash flow support",
            "monthly_income": 1800,
            "monthly_expenses": 700,
            "existing_loan_obligations": 100,
            "employment_status": "Employed",
            "employer_name": "Bluewave Co",
            "bank_name": "KCB",
            "account_type": "Current",
        },
        {
            "application_number": "APP-003",
            "applicant_user_id": john.id,
            "loan_product_id": small_business_loan.id,
            "status": "rejected",
            "requested_amount": 10000,
            "requested_term_months": 18,
            "loan_purpose": "Expand shop inventory",
            "monthly_income": 1500,
            "monthly_expenses": 1100,
            "existing_loan_obligations": 400,
            "employment_status": "Self Employed",
            "employer_name": "John Ventures",
            "bank_name": "Co-op Bank",
            "account_type": "Business",
        },
    ]

    for app_data in applications:
        existing_application = (
            db.query(Application)
            .filter(Application.application_number == app_data["application_number"])
            .first()
        )
        if not existing_application:
            db.add(Application(**app_data))

    db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        seed_users(db)
        seed_loan_products(db)
        seed_applications(db)
        print("Seed data inserted successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()