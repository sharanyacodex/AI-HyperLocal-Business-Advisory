"""
routes/financial.py

Purpose:
    Exposes the Financial Engine over HTTP as a FastAPI route.

    This file is intentionally "thin": it does NOT calculate anything
    itself. It only:
        1. Accepts and validates the request body (via FinancialCalculationInput)
        2. Calls the deterministic calculation service (calculate_financials)
        3. Returns the structured response (FinancialCalculationResponse)

    All financial math lives in services/financial_service.py.
    No Gemini/OpenAI/LLM calls happen anywhere in this file.
"""

from fastapi import APIRouter, HTTPException

from models.financial import FinancialCalculationInput, FinancialCalculationResponse
from services.financial_service import calculate_financials

router = APIRouter(
    prefix="/api/module2/financial",
    tags=["Module 2 - Financial Engine"],
)


@router.post("/calculate", response_model=FinancialCalculationResponse)
def calculate_financial_summary(data: FinancialCalculationInput) -> FinancialCalculationResponse:
    """
    Calculates project cost, loan amount, EMI, and repayment/DSCR figures
    for a single applicant, based on validated input.

    Validation (invalid contribution_rate, negative values, etc.) is
    already handled by FinancialCalculationInput before this function
    body even runs. If validation fails, FastAPI automatically returns
    a 422 error with details, and this function is never called.
    """
    try:
        return calculate_financials(data)
    except ZeroDivisionError:
        raise HTTPException(
            status_code=400,
            detail="Unable to calculate: contribution_rate resulted in a division error.",
        )