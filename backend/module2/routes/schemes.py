from fastapi import APIRouter, HTTPException

from models.scheme_matching import (
    SchemeMatchingInput,
    SchemeMatchResponse,
)
from services.scheme_service import match_schemes


router = APIRouter(
    prefix="/api/v1/schemes",
    tags=["Schemes"],
)


@router.post("/match", response_model=SchemeMatchResponse)
def match_government_schemes(data: SchemeMatchingInput):
    try:
        result = match_schemes(
            requested_loan_amount=data.requested_loan_amount,
            beneficiary_category=data.beneficiary_category,
            location_type=data.location_type,
            business_sector=data.business_sector,
            tarun_plus_eligible=data.tarun_plus_eligible,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scheme matching failed: {str(e)}",
        )