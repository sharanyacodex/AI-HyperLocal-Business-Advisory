"""
models/financial.py

Purpose:
    Defines the data shapes (Pydantic models) used by the Financial Engine.

    - FinancialCalculationInput      -> what the user/frontend sends us
    - FinancialSummary               -> calculated project/loan numbers
    - RepaymentSummary               -> calculated repayment/DSCR numbers
    - FinancialCalculationResponse   -> complete API response

Important:
    Scheme-dependent financial values must come from verified scheme rules.

    Some government schemes may not provide a fixed value for:
        - contribution rate
        - loan limit
        - interest rate
        - tenure

    Therefore, these fields are Optional. The financial engine must never
    invent missing government scheme values.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FinancialCalculationInput(BaseModel):
    selected_scheme: Optional[str] = Field(
        default=None,
        description=(
            "Scheme code selected by the user, for example PMMY or PMEGP."
        ),
    )

    available_margin: float = Field(
        ...,
        gt=0,
        description=(
            "Beneficiary's own available margin/capital. Must be greater than 0."
        ),
    )

    contribution_rate: float = Field(
        ...,
        gt=0,
        lt=1,
        description=(
            "Beneficiary's required contribution rate as a fraction "
            "(for example 0.10 for 10%). Must come from a verified "
            "scheme rule."
        ),
    )

    project_cost_limit: float = Field(
        ...,
        gt=0,
        description=(
            "Maximum project cost allowed under the applicable "
            "verified scheme rule."
        ),
    )

    loan_limit: Optional[float] = Field(
        default=None,
        gt=0,
        description=(
            "Maximum loan amount allowed under the applicable scheme rule. "
            "None means no fixed scheme-level loan limit is available "
            "in the verified scheme data."
        ),
    )

    interest_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description=(
            "Annual interest rate as a percentage. "
            "Must come from verified scheme/lending-institution data. "
            "None means no fixed verified rate is available."
        ),
    )

    tenure_months: Optional[int] = Field(
        default=None,
        gt=0,
        le=600,
        description=(
            "Loan tenure in months. "
            "None means no fixed verified tenure is available."
        ),
    )

    monthly_revenue: float = Field(
        ...,
        ge=0,
        description=(
            "Expected or actual monthly business revenue."
        ),
    )

    monthly_operating_cost: float = Field(
        ...,
        ge=0,
        description=(
            "Expected or actual monthly operating cost."
        ),
    )

    @field_validator("contribution_rate")
    @classmethod
    def contribution_rate_must_be_realistic(cls, v: float) -> float:
        if v <= 0 or v >= 1:
            raise ValueError(
                "contribution_rate must be strictly between 0 and 1 "
                "(exclusive)."
            )
        return v


class FinancialSummary(BaseModel):
    theoretical_project_capacity: float
    final_project_cost: float
    beneficiary_contribution: float
    loan_amount: float

    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None

    emi: Optional[float] = None
    total_interest: Optional[float] = None


class RepaymentSummary(BaseModel):
    monthly_revenue: float
    monthly_operating_cost: float
    operating_surplus: float

    dscr: Optional[float] = Field(
        default=None,
        description=(
            "Application-level repayment stress indicator. "
            "Null when EMI cannot be calculated or there is no debt service."
        ),
    )

    stress_level: str = Field(
        description=(
            "Application-level classification label, such as "
            "'healthy', 'watch', or 'high_stress'. "
            "This is not a banking standard."
        ),
    )


class FinancialCalculationResponse(BaseModel):
    success: bool

    financial_summary: FinancialSummary

    repayment: RepaymentSummary
