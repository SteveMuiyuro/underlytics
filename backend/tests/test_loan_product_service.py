from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from underlytics_api.models.base import Base
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.services.loan_product_service import (
    DEFAULT_LOAN_PRODUCTS,
    ensure_default_loan_products,
)


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()


def test_ensure_default_loan_products_creates_bootstrap_records():
    db = make_session()

    try:
        created_count = ensure_default_loan_products(db)
        product_codes = sorted(product.code for product in db.query(LoanProduct).all())
    finally:
        db.close()

    assert created_count == len(DEFAULT_LOAN_PRODUCTS)
    assert product_codes == sorted(product["code"] for product in DEFAULT_LOAN_PRODUCTS)


def test_ensure_default_loan_products_is_idempotent():
    db = make_session()

    try:
        ensure_default_loan_products(db)
        created_count = ensure_default_loan_products(db)
        total_products = db.query(LoanProduct).count()
    finally:
        db.close()

    assert created_count == 0
    assert total_products == len(DEFAULT_LOAN_PRODUCTS)
