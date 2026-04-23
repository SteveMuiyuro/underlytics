from pydantic import BaseModel


class LoanProductResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    min_amount: int
    max_amount: int
    min_term_months: int
    max_term_months: int
    is_active: bool

    model_config = {"from_attributes": True}