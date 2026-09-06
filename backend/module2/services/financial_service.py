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
    """
    Calculate monthly EMI using the reducing-balance formula.

    annual_interest_rate_percent is expressed as a percentage.
    Example: 8 means 8% annual interest.
    """

    if principal <= 0:
        return 0.0

    if tenure_months <= 0:
        raise ValueError("tenure_months must be greater than 0.")

    if annual_interest_rate_percent == 0:
        return principal / tenure_months

    monthly_rate = annual_interest_rate_percent / 100 / 12

    emi = (
        principal
        * monthly_rate
        * (1 + monthly_rate) ** tenure_months
        / ((1 + monthly_rate) ** tenure_months - 1)
    )

    return emi


def classify_stress_level(dscr: float | None) -> str:
    """
    Application-level repayment stress classification.

    This is NOT a banking standard.
    """

    if dscr is None:
        return "not_applicable"

    if dscr > 1.5:
        return "healthy"

    if dscr >= 1.2:
        return "watch"

    if dscr >= 1.0:
        return "high_stress"

    return "very_high_stress"


def calculate_financials(
    data: FinancialCalculationInput,
) -> FinancialCalculationResponse:

    # ---------------------------------------------------------
    # STEP 1: Maximum project capacity
    # ---------------------------------------------------------

    theoretical_project_capacity = (
        data.available_margin / data.contribution_rate
    )

    # ---------------------------------------------------------
    # STEP 2: Maximum affordable loan
    # ---------------------------------------------------------

    maximum_affordable_loan = (
        theoretical_project_capacity
        * (1 - data.contribution_rate)
    )

    # ---------------------------------------------------------
    # STEP 3: Determine final project and loan amount
    # ---------------------------------------------------------

    if data.requested_loan_amount is not None:

        requested_loan = data.requested_loan_amount

        # Bank financing percentage
        bank_financing_rate = 1 - data.contribution_rate

        # Required project cost for requested loan
        requested_project_cost = (
            requested_loan / bank_financing_rate
        )

        # Required beneficiary contribution
        required_contribution = (
            requested_project_cost
            * data.contribution_rate
        )

        # Check available margin
        if required_contribution > data.available_margin:
            raise ValueError(
                "Requested loan amount exceeds the beneficiary's "
                "available margin."
            )

        # Check project-cost limit
        if requested_project_cost > data.project_cost_limit:
            raise ValueError(
                "Requested loan amount exceeds the scheme's "
                "project cost limit."
            )

        # Check loan limit
        if (
            data.loan_limit is not None
            and requested_loan > data.loan_limit
        ):
            raise ValueError(
                "Requested loan amount exceeds the scheme's "
                "loan limit."
            )

        final_project_cost = requested_project_cost
        beneficiary_contribution = required_contribution
        loan_amount = requested_loan

    else:

        # No requested loan:
        # calculate maximum possible project size.

        final_project_cost = min(
            theoretical_project_capacity,
            data.project_cost_limit,
        )

        beneficiary_contribution = (
            final_project_cost
            * data.contribution_rate
        )

        loan_amount = (
            final_project_cost
            - beneficiary_contribution
        )

        # Apply loan limit if available
        if (
            data.loan_limit is not None
            and loan_amount > data.loan_limit
        ):
            loan_amount = data.loan_limit

            final_project_cost = (
                loan_amount
                / (1 - data.contribution_rate)
            )

            beneficiary_contribution = (
                final_project_cost
                * data.contribution_rate
            )

    # ---------------------------------------------------------
    # STEP 4: EMI
    # ---------------------------------------------------------

    emi = None
    total_interest = None

    if (
        data.interest_rate is not None
        and data.tenure_months is not None
    ):
        emi = calculate_emi(
            principal=loan_amount,
            annual_interest_rate_percent=data.interest_rate,
            tenure_months=data.tenure_months,
        )

        total_payment = emi * data.tenure_months
        total_interest = total_payment - loan_amount

    # ---------------------------------------------------------
    # STEP 5: Operating surplus
    # ---------------------------------------------------------

    operating_surplus = (
        data.monthly_revenue
        - data.monthly_operating_cost
    )

    # ---------------------------------------------------------
    # STEP 6: DSCR
    # ---------------------------------------------------------

    dscr = None

    if emi is not None and emi > 0:
        dscr = operating_surplus / emi

    stress_level = classify_stress_level(dscr)

    # ---------------------------------------------------------
    # STEP 7: Response
    # ---------------------------------------------------------

    financial_summary = FinancialSummary(
        theoretical_project_capacity=theoretical_project_capacity,
        maximum_affordable_loan=maximum_affordable_loan,
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