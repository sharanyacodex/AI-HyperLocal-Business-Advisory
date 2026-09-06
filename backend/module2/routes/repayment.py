"""
routes/repayment.py

Purpose:
    Exposes the Repayment Stress Testing engine over HTTP.

    This file is intentionally thin: it does NOT calculate anything
    itself. It only:
        1. Accepts and validates the request body (reusing
           FinancialCalculationInput from models/financial.py)
        2. Calls run_stress_test() (services/repayment_service.py)
        3. Returns the structured response (StressTestResponse)

    No Gemini/OpenAI/LLM calls happen anywhere in this file.
"""

from fastapi import APIRouter

from models.financial import FinancialCalculationInput
from models.repayment import StressTestResponse
from services.repayment_service import run_stress_test

router = APIRouter(
    prefix="/api/module2/repayment",
    tags=["Module 2 - Repayment Stress Testing"],
)


@router.post("/stress-test", response_model=StressTestResponse)
def stress_test(data: FinancialCalculationInput) -> StressTestResponse:
    """
    Runs base / moderate / severe repayment stress scenarios for a single
    applicant. Validation of the input (contribution_rate, interest_rate,
    tenure_months, etc.) is already handled by FinancialCalculationInput
    before this function body runs.
    """
    return run_stress_test(data)