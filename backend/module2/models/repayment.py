"""
models/repayment.py

Purpose:
    Response models for the repayment stress-testing feature.

    No new request model is defined here. The stress-test endpoint reuses
    FinancialCalculationInput (from models/financial.py) as its request
    body, because deriving the stress scenarios requires the exact same
    underlying inputs (margin, scheme limits, interest rate, tenure,
    revenue, cost) that the financial calculator already needs.

Reminder (application-level indicator, not a banking standard):
    We use DSCR as an application-level repayment stress indicator.
    The stress_level thresholds are application-level configurable
    settings for this MVP, defined in services/financial_service.py's
    classify_stress_level() function -- they are reused here, not
    redefined.
"""

from pydantic import BaseModel
from typing import Optional


class ScenarioResult(BaseModel):
    """
    Result of one stress scenario (base / moderate / severe).
    """

    monthly_revenue: float
    monthly_operating_cost: float
    operating_surplus: float
    emi: float
    dscr: Optional[float] = None
    stress_level: str


class StressTestResponse(BaseModel):
    """
    Full response returned by POST /api/module2/repayment/stress-test
    """

    success: bool
    base: ScenarioResult
    moderate: ScenarioResult
    severe: ScenarioResult