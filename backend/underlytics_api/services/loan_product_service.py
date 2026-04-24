from sqlalchemy.orm import Session

from underlytics_api.models.loan_product import LoanProduct

DEFAULT_LOAN_PRODUCTS = [
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


def ensure_default_loan_products(db: Session) -> int:
    created_count = 0

    for product_data in DEFAULT_LOAN_PRODUCTS:
        existing_product = (
            db.query(LoanProduct).filter(LoanProduct.code == product_data["code"]).first()
        )
        if existing_product:
            continue

        db.add(LoanProduct(**product_data))
        created_count += 1

    if created_count:
        db.commit()

    return created_count
