"""
models/financial.py

Purpose:
    Defines the data shapes (Pydantic models) used by the Financial Engine.

    - FinancialCalculationInput  -> what the user/frontend sends us
    - FinancialSummary           -> the calculated project/loan numbers
    - RepaymentSummary           -> the calculated repayment/DSCR numbers
    - FinancialCalculationResponse -> the full API response shape

Why Pydantic?
    Pydantic checks incoming data BEFORE it reaches our calculation code.
    If someone sends a negative number or an invalid rate, FastAPI will
    automatically reject the request with a clear error message. This
    keeps the calculation logic (Phase 2) simple and safe, because it can
    always assume the numbers it receives are already valid.

Note on selected_scheme:
    This field is a placeholder for now. It will be used starting in
    Phase 6+ once the Government Scheme Engine exists. Until then, the
    financial engine is tested using directly-supplied contribution_rate,
    interest_rate, tenure_months, and limits (so we don't have a hard
    dependency on the scheme engine yet).
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class FinancialCalculationInput(BaseModel):
    selected_scheme: Optional[str] = Field(
        default=None,
        description="Scheme code selected by the user. Not used until the "
                    "Scheme Engine (Phase 6+) is connected.",
    )

    available_margin: float = Field(
        ...,
        gt=0,
        description="Beneficiary's own available margin/capital (must be > 0).",
    )

    contribution_rate: float = Field(
        ...,
        gt=0,
        lt=1,
        description="Beneficiary's required contribution rate as a fraction "
                    "(e.g. 0.10 for 10%). Must come from a verified scheme "
                    "rule. Must be strictly between 0 and 1.",
    )

    project_cost_limit: float = Field(
        ...,
        gt=0,
        description="Maximum project cost allowed under the applicable "
                    "scheme rule (must be > 0).",
    )

    loan_limit: float = Field(
        ...,
        gt=0,
        description="Maximum loan amount allowed under the applicable "
                    "scheme rule (must be > 0).",
    )

    interest_rate: float = Field(
        ...,
        ge=0,
        le=100,
        description="Annual interest rate as a percentage (e.g. 8.5 for "
                    "8.5%). Must be verified scheme data, never guessed.",
    )

    tenure_months: int = Field(
        ...,
        gt=0,
        le=600,
        description="Loan tenure in months (must be a positive whole "
                    "number; capped at 600 months / 50 years as a sanity "
                    "limit).",
    )

    monthly_revenue: float = Field(
        ...,
        ge=0,
        description="Expected/actual monthly revenue of the business.",
    )

    monthly_operating_cost: float = Field(
        ...,
        ge=0,
        description="Expected/actual monthly operating cost of the business.",
    )

    @field_validator("contribution_rate")
    @classmethod
    def contribution_rate_must_be_realistic(cls, v: float) -> float:
        if v <= 0 or v >= 1:
            raise ValueError(
                "contribution_rate must be strictly between 0 and 1 (exclusive)."
            )
        return v


class FinancialSummary(BaseModel):
    theoretical_project_capacity: float
    final_project_cost: float
    beneficiary_contribution: float
    loan_amount: float
    interest_rate: float
    tenure_months: int
    emi: float
    total_interest: float


class RepaymentSummary(BaseModel):
    monthly_revenue: float
    monthly_operating_cost: float
    operating_surplus: float
    dscr: Optional[float] = Field(
        default=None,
        description="Null when debt service is zero (e.g. loan_amount is 0), "
                    "since DSCR is undefined in that case.",
    )
    stress_level: str = Field(
        description="Application-level classification label, e.g. "
                    "'healthy', 'watch', 'high_stress'. Not a banking standard."
    )


class FinancialCalculationResponse(BaseModel):
    success: bool
    financial_summary: FinancialSummary
    repayment: RepaymentSummary