"""
services/integration_service.py

Purpose:
    Connects the Scheme Matcher with the existing Financial Engine.

Flow:
    Scheme Matcher
        ↓
    User-selected scheme
        ↓
    Resolve scheme-dependent financial rules
        ↓
    Existing calculate_financials()
        ↓
    Existing classify_stress_level()

Important:
    This service does NOT perform financial calculations itself.
    All financial calculations are delegated to financial_service.py.
"""

from typing import Any

from models.financial import FinancialCalculationInput
from services.financial_service import (
    calculate_financials,
    classify_stress_level,
)
from services.scheme_service import match_schemes


def _resolve_value(
    scheme_match: dict[str, Any],
    field_name: str,
    manual_overrides: dict[str, Any],
) -> tuple[Any, bool]:
    """
    Resolve a scheme-dependent value.

    Priority:
        1. Verified scheme data
        2. Explicit manual override
        3. None

    Returns:
        (value, used_manual_override)
    """

    scheme_value = scheme_match.get(field_name)

    if scheme_value is not None:
        return scheme_value, False

    override_value = manual_overrides.get(field_name)

    if override_value is not None:
        return override_value, True

    return None, False


def evaluate_integration(data) -> dict[str, Any]:
    """
    Match schemes, validate the user's selected scheme, resolve
    financial inputs, and delegate calculations to the existing
    Financial Engine.
    """

    # ---------------------------------------------------------
    # 1. Match available schemes
    # ---------------------------------------------------------

    scheme_result = match_schemes(
        requested_loan_amount=data.requested_loan_amount,
        beneficiary_category=data.beneficiary_category,
        location_type=data.location_type,
        business_sector=data.business_sector,
        tarun_plus_eligible=data.tarun_plus_eligible,
    )

    matches = scheme_result.get("matches", [])

    # ---------------------------------------------------------
    # 2. Require explicit scheme selection
    # ---------------------------------------------------------

    selected_scheme_code = data.selected_scheme_code.strip().upper()

    selected_match = None

    for scheme in matches:
        if scheme.get("scheme_code", "").upper() == selected_scheme_code:
            selected_match = scheme
            break

    if selected_match is None:
        raise ValueError(
            f"Selected scheme '{selected_scheme_code}' "
            "was not found among the matched schemes."
        )

    # ---------------------------------------------------------
    # 3. Prepare manual overrides
    # ---------------------------------------------------------

    manual_overrides = {}

    if data.manual_overrides is not None:
        manual_overrides = data.manual_overrides.model_dump(
            exclude_none=True
        )

    used_manual_overrides = []

    # ---------------------------------------------------------
    # 4. Resolve scheme-dependent financial values
    # ---------------------------------------------------------

    contribution_rate, used = _resolve_value(
        selected_match,
        "contribution_rate",
        manual_overrides,
    )

    if used:
        used_manual_overrides.append("contribution_rate")

    project_cost_limit, used = _resolve_value(
        selected_match,
        "maximum_project_cost",
        manual_overrides,
    )

    if used:
        used_manual_overrides.append("project_cost_limit")

    loan_limit, used = _resolve_value(
        selected_match,
        "maximum_loan_amount",
        manual_overrides,
    )

    if used:
        used_manual_overrides.append("loan_limit")

    interest_rate, used = _resolve_value(
        selected_match,
        "interest_rate",
        manual_overrides,
    )

    if used:
        used_manual_overrides.append("interest_rate")

    tenure_months, used = _resolve_value(
        selected_match,
        "tenure_months",
        manual_overrides,
    )

    if used:
        used_manual_overrides.append("tenure_months")

    # ---------------------------------------------------------
    # 5. Identify required missing values
    # ---------------------------------------------------------

    missing_fields = []

    if contribution_rate is None:
        missing_fields.append("contribution_rate")

    if project_cost_limit is None:
        missing_fields.append("project_cost_limit")

    # ---------------------------------------------------------
    # 6. Calculate operating surplus even if EMI is unavailable
    # ---------------------------------------------------------

    operating_surplus = (
        data.monthly_revenue - data.monthly_operating_cost
    )

    # ---------------------------------------------------------
    # 7. If required financial inputs are missing,
    #    do NOT call the financial engine.
    # ---------------------------------------------------------

    if missing_fields:

        dscr = None
        stress_level = classify_stress_level(dscr)

        return {
            "success": False,
            "selected_scheme_code": selected_scheme_code,
            "scheme_match": selected_match,
            "financial_summary": None,
            "repayment": {
                "monthly_revenue": data.monthly_revenue,
                "monthly_operating_cost": data.monthly_operating_cost,
                "operating_surplus": operating_surplus,
                "dscr": dscr,
                "stress_level": stress_level,
            },
            "missing_fields": missing_fields,
            "used_manual_overrides": used_manual_overrides,
            "subsidy_rate": selected_match.get("subsidy_rate"),
            "message": (
                "Financial calculation could not be completed because "
                "required scheme-dependent values are unavailable."
            ),
        }

    # ---------------------------------------------------------
    # 8. Build the EXISTING FinancialCalculationInput
    # ---------------------------------------------------------

    financial_input = FinancialCalculationInput(
        selected_scheme=selected_scheme_code,
        requested_loan_amount=data.requested_loan_amount,
        available_margin=data.available_margin,
        contribution_rate=contribution_rate,
        project_cost_limit=project_cost_limit,
        loan_limit=loan_limit,
        interest_rate=interest_rate,
        tenure_months=tenure_months,
        monthly_revenue=data.monthly_revenue,
        monthly_operating_cost=data.monthly_operating_cost,
    )

    # ---------------------------------------------------------
    # 9. Delegate ALL financial calculations
    #    to the existing Financial Engine.
    # ---------------------------------------------------------

    financial_result = calculate_financials(financial_input)

    # ---------------------------------------------------------
    # 10. Return the complete integrated result
    # ---------------------------------------------------------

    return {
        "success": True,
        "selected_scheme_code": selected_scheme_code,
        "scheme_match": selected_match,
        "financial_summary": financial_result.financial_summary.model_dump(),
        "repayment": financial_result.repayment.model_dump(),
        "missing_fields": [],
        "used_manual_overrides": used_manual_overrides,
        "subsidy_rate": selected_match.get("subsidy_rate"),
        "message": (
            "Scheme matching and deterministic financial calculation "
            "completed successfully."
        ),
    }