"""
services/repayment_service.py

Purpose:
    Deterministic repayment stress-testing engine.

    This file does NOT duplicate EMI or stress-classification logic.
    It reuses:
        - calculate_financials()   (from services/financial_service.py)
          to get the loan_amount and EMI for the applicant.
        - classify_stress_level()  (from services/financial_service.py)
          to label each scenario's DSCR consistently with the main
          financial engine.

    No Gemini/OpenAI/LLM calls happen anywhere in this file.

We use DSCR as an application-level repayment stress indicator.
These are NOT banking-industry thresholds; they are configurable
application settings defined once in financial_service.py.
"""

from typing import Dict, Tuple

from models.financial import FinancialCalculationInput
from models.repayment import ScenarioResult, StressTestResponse
from services.financial_service import calculate_financials, classify_stress_level

# Application-level stress scenarios (NOT banking standards).
# Each scenario is defined as (revenue_factor, cost_factor).
STRESS_SCENARIOS: Dict[str, Tuple[float, float]] = {
    "base": (1.0, 1.0),         # No change
    "moderate": (0.8, 1.10),    # Revenue -20%, cost +10%
    "severe": (0.6, 1.20),      # Revenue -40%, cost +20%
}


def _build_scenario(
    monthly_revenue: float,
    monthly_operating_cost: float,
    emi: float,
    revenue_factor: float,
    cost_factor: float,
) -> ScenarioResult:
    """
    Builds a single stress scenario result.

    EMI is held constant across all scenarios: stress testing changes
    revenue and operating cost, not the loan terms themselves.
    """
    revenue = monthly_revenue * revenue_factor
    cost = monthly_operating_cost * cost_factor
    operating_surplus = revenue - cost

    if emi == 0:
        dscr = None
    else:
        dscr = operating_surplus / emi

    stress_level = classify_stress_level(dscr)

    return ScenarioResult(
        monthly_revenue=revenue,
        monthly_operating_cost=cost,
        operating_surplus=operating_surplus,
        emi=emi,
        dscr=dscr,
        stress_level=stress_level,
    )


def run_stress_test(data: FinancialCalculationInput) -> StressTestResponse:
    """
    Runs base / moderate / severe stress scenarios for a single applicant.

    Step 1: Reuse the existing financial engine to get the EMI that would
             apply to this applicant (same loan/EMI logic as the main
             /financial/calculate endpoint -- not recalculated here).
    Step 2: Apply each scenario's revenue/cost stress factors.
    Step 3: Classify each scenario's DSCR using the same thresholds as
             the main financial engine.
    """
    financial_result = calculate_financials(data)
    emi = financial_result.financial_summary.emi

    scenario_results = {}
    for scenario_name, (revenue_factor, cost_factor) in STRESS_SCENARIOS.items():
        scenario_results[scenario_name] = _build_scenario(
            monthly_revenue=data.monthly_revenue,
            monthly_operating_cost=data.monthly_operating_cost,
            emi=emi,
            revenue_factor=revenue_factor,
            cost_factor=cost_factor,
        )

    return StressTestResponse(
        success=True,
        base=scenario_results["base"],
        moderate=scenario_results["moderate"],
        severe=scenario_results["severe"],
    )