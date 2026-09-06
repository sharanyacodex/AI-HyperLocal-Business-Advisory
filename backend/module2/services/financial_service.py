"""
services/financial_service.py

Purpose:
    Deterministic financial calculation engine for Module 2.

    This file NEVER uses Gemini, OpenAI, or any LLM. Every number here is
    plain Python arithmetic so that the same input always produces the
    same output (required for auditability in a government-facing tool).

    Pipeline implemented here:
        available_margin + contribution_rate
            -> theoretical_project_capacity
            -> final_project_cost (capped by scheme project_cost_limit)
            -> beneficiary_contribution
            -> loan_amount (capped by scheme loan_limit)
            -> EMI
            -> total_interest
            -> operating_surplus
            -> DSCR
            -> stress_level (application-level label, not a banking standard)

Important:
    contribution_rate, project_cost_limit, loan_limit, and interest_rate
    are NOT invented here. They must come from a verified government
    scheme rule (wired in from Phase 6+ onward). For now they arrive
    directly on FinancialCalculationInput so this engine can be built and
    tested independently of the Scheme Engine.
"""

from models.financial import (
    FinancialCalculationInput,
    FinancialCalculationResponse,
    FinancialSummary,
    RepaymentSummary,
)


def calculate_emi(principal: float, annual_interest_rate_percent: float, tenure_months: int) -> float:
    """
    Calculates EMI using the standard reducing-balance formula:

        EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)

    where:
        P = principal (loan_amount)
        r = monthly interest rate (annual_rate / 12 / 100)
        n = tenure in months

    Special case: if annual_interest_rate_percent is 0, EMI is a simple
    straight-line division (avoids divide-by-zero in the formula above).
    """
    if principal <= 0:
        # No loan needed -> no EMI.
        return 0.0

    if annual_interest_rate_percent == 0:
        return principal / tenure_months

    monthly_rate = annual_interest_rate_percent / 12 / 100
    growth_factor = (1 + monthly_rate) ** tenure_months

    emi = principal * monthly_rate * growth_factor / (growth_factor - 1)
    return emi


def classify_stress_level(dscr):
    """
    Classifies DSCR into an APPLICATION-LEVEL stress label.

    IMPORTANT: These thresholds are configurable application settings
    defined for this project's MVP. They are NOT an official banking
    standard. If these thresholds change, update only this function.
    """
    if dscr is None:
        return "not_applicable"

    if dscr > 1.5:
        return "healthy"
    elif 1.2 <= dscr <= 1.5:
        return "watch"
    elif 1.0 <= dscr < 1.2:
        return "high_stress"
    else:
        return "very_high_stress"


def calculate_financials(data: FinancialCalculationInput) -> FinancialCalculationResponse:
    """
    Runs the full deterministic financial calculation pipeline for a
    single user input and returns a structured, validated response.
    """

    # Step A: Theoretical project capacity
    theoretical_project_capacity = data.available_margin / data.contribution_rate

    # Step B: Final project cost (capped by scheme's project cost limit)
    final_project_cost = min(theoretical_project_capacity, data.project_cost_limit)

    # Step C: Beneficiary contribution (based on the FINAL project cost,
    # not the theoretical one, so the numbers stay internally consistent)
    beneficiary_contribution = final_project_cost * data.contribution_rate

    # Step D: Loan amount, never negative, never above the scheme's loan limit
    raw_loan_amount = final_project_cost - beneficiary_contribution
    loan_amount = max(0.0, min(raw_loan_amount, data.loan_limit))

    # Step E: EMI
    emi = calculate_emi(
        principal=loan_amount,
        annual_interest_rate_percent=data.interest_rate,
        tenure_months=data.tenure_months,
    )

    # Step F: Total interest paid over the life of the loan
    total_interest = (emi * data.tenure_months) - loan_amount

    # Step G: Operating surplus (can be negative — that's meaningful, not an error)
    operating_surplus = data.monthly_revenue - data.monthly_operating_cost

    # Step H: DSCR (undefined, i.e. None, when there is no EMI to service)
    if emi == 0:
        dscr = None
    else:
        dscr = operating_surplus / emi

    # Step I: Stress level label (application-level, not a banking standard)
    stress_level = classify_stress_level(dscr)

    financial_summary = FinancialSummary(
        theoretical_project_capacity=theoretical_project_capacity,
        final_project_cost=final_project_cost,
        beneficiary_contribution=beneficiary_contribution,
        loan_amount=loan_amount,
        interest_rate=data.interest_rate,
        tenure_months=data.tenure_months,
        emi=emi,
        total_interest=total_interest,
    )

    repayment = RepaymentSummary(
        monthly_revenue=data.monthly_revenue,
        monthly_operating_cost=data.monthly_operating_cost,
        operating_surplus=operating_surplus,
        dscr=dscr,
        stress_level=stress_level,
    )

    return FinancialCalculationResponse(
        success=True,
        financial_summary=financial_summary,
        repayment=repayment,
    )