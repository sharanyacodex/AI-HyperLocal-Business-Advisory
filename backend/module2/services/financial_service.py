from models.financial import (
    FinancialCalculationInput,
    FinancialCalculationResponse,
    FinancialSummary,
    RepaymentSummary,
)


def calculate_emi(
    principal: float,
    annual_interest_rate_percent: float,
    tenure_months: int,
) -> float:

    if principal <= 0:
        return 0.0

    if annual_interest_rate_percent == 0:
        return principal / tenure_months

    monthly_rate = annual_interest_rate_percent / 12 / 100

    growth_factor = (1 + monthly_rate) ** tenure_months

    emi = (
        principal
        * monthly_rate
        * growth_factor
        / (growth_factor - 1)
    )

    return emi


def classify_stress_level(dscr):
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


def calculate_financials(
    data: FinancialCalculationInput,
) -> FinancialCalculationResponse:

    # ---------------------------------------------------------
    # Step A: Theoretical project capacity
    # ---------------------------------------------------------

    theoretical_project_capacity = (
        data.available_margin / data.contribution_rate
    )

    # ---------------------------------------------------------
    # Step B: Final project cost
    # ---------------------------------------------------------

    final_project_cost = min(
        theoretical_project_capacity,
        data.project_cost_limit,
    )

    # ---------------------------------------------------------
    # Step C: Beneficiary contribution
    # ---------------------------------------------------------

    beneficiary_contribution = (
        final_project_cost * data.contribution_rate
    )

    # ---------------------------------------------------------
    # Step D: Final project cost and loan amount
    # ---------------------------------------------------------

    raw_loan_amount = (
        final_project_cost - beneficiary_contribution
    )

    if (
        data.loan_limit is not None
        and raw_loan_amount > data.loan_limit
    ):

        final_project_cost = min(
            final_project_cost,
            data.loan_limit / (1 - data.contribution_rate),
        )

        beneficiary_contribution = (
            final_project_cost * data.contribution_rate
        )

        loan_amount = (
            final_project_cost - beneficiary_contribution
        )

    else:
        loan_amount = max(0.0, raw_loan_amount)

    # ---------------------------------------------------------
    # Step E: EMI
    # ---------------------------------------------------------

    if (
        data.interest_rate is not None
        and data.tenure_months is not None
    ):

        emi = calculate_emi(
            principal=loan_amount,
            annual_interest_rate_percent=data.interest_rate,
            tenure_months=data.tenure_months,
        )

        # -----------------------------------------------------
        # Step F: Total interest
        # -----------------------------------------------------

        total_interest = (
            emi * data.tenure_months
        ) - loan_amount

    else:
        emi = None
        total_interest = None

    # ---------------------------------------------------------
    # Step G: Operating surplus
    # ---------------------------------------------------------

    operating_surplus = (
        data.monthly_revenue
        - data.monthly_operating_cost
    )

    # ---------------------------------------------------------
    # Step H: DSCR
    # ---------------------------------------------------------

    if emi is None or emi == 0:
        dscr = None
    else:
        dscr = operating_surplus / emi

    # ---------------------------------------------------------
    # Step I: Stress classification
    # ---------------------------------------------------------

    stress_level = classify_stress_level(dscr)

    # ---------------------------------------------------------
    # Financial summary
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Repayment summary
    # ---------------------------------------------------------

    repayment = RepaymentSummary(
        monthly_revenue=data.monthly_revenue,
        monthly_operating_cost=data.monthly_operating_cost,
        operating_surplus=operating_surplus,
        dscr=dscr,
        stress_level=stress_level,
    )

    # ---------------------------------------------------------
    # Final response
    # ---------------------------------------------------------

    return FinancialCalculationResponse(
        success=True,
        financial_summary=financial_summary,
        repayment=repayment,
    )