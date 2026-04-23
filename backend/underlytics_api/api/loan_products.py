from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from underlytics_api.db.dependencies import get_db
from underlytics_api.models.loan_product import LoanProduct
from underlytics_api.schemas.loan_product import LoanProductResponse

router = APIRouter(prefix="/api/loan-products", tags=["Loan Products"])


@router.get("", response_model=list[LoanProductResponse])
def list_loan_products(db: Session = Depends(get_db)):
    return db.query(LoanProduct).filter(LoanProduct.is_active).all()
