from pydantic import BaseModel, Field


class SchemeMatchingInput(BaseModel):
    requested_loan_amount: float = Field(gt=0)

    beneficiary_category: str
    location_type: str
    business_sector: str

    tarun_plus_eligible: bool = False


class SchemeMatchResponse(BaseModel):
    success: bool
    requested_loan_amount: float
    total_matches: int
    matches: list[dict]