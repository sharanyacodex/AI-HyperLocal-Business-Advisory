"""
models/integration.py

Purpose:
    Defines request and response models for the Module 2 integration layer.

    The integration layer connects:
        Scheme Matcher
            ↓
        Selected Scheme
            ↓
        Financial Engine
            ↓
        Repayment / DSCR stress indicator

Important:
    The integration layer must never invent government scheme values.
    Missing scheme-dependent values must be reported instead.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ManualOverrides(BaseModel):
    """
    Optional caller/lender-provided assumptions.

    These values are NOT treated as verified government scheme rules.
    They are used only when the selected scheme does not provide
    the required value.
    """

    contribution_rate: Optional[float] = Field(
        default=None,
        gt=0,
        lt=1,
        description="Caller/lender-provided beneficiary contribution rate.",
    )

    project_cost_limit: Optional[float] = Field(
        default=None,
        gt=0,
        description="Caller/lender-provided project cost limit.",
    )

    loan_limit: Optional[float] = Field(
        default=None,
        gt=0,
        description="Caller/lender-provided loan limit.",
    )

    interest_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Caller/lender-provided annual interest rate.",
    )

    tenure_months: Optional[int] = Field(
        default=None,
        gt=0,
        le=600,
        description="Caller/lender-provided loan tenure in months.",
    )


class IntegrationInput(BaseModel):
    """
    Input required to connect scheme matching with financial calculation.
    """

    requested_loan_amount: float = Field(
        ...,
        gt=0,
        description="Loan amount the applicant wants to request.",
    )

    beneficiary_category: str = Field(
        ...,
        min_length=1,
        description="Beneficiary category used by the scheme matcher.",
    )

    location_type: str = Field(
        ...,
        min_length=1,
        description="Location type, such as rural or urban.",
    )

    business_sector: str = Field(
        ...,
        min_length=1,
        description="Business sector used by the scheme matcher.",
    )

    tarun_plus_eligible: bool = Field(
        default=False,
        description="Whether the applicant is eligible for PMMY Tarun Plus.",
    )

    selected_scheme_code: str = Field(
        ...,
        min_length=1,
        description="Scheme explicitly selected by the user.",
    )

    available_margin: float = Field(
        ...,
        gt=0,
        description="Applicant's available own margin/capital.",
    )

    monthly_revenue: float = Field(
        ...,
        ge=0,
        description="Expected or actual monthly business revenue.",
    )

    monthly_operating_cost: float = Field(
        ...,
        ge=0,
        description="Expected or actual monthly operating cost.",
    )

    manual_overrides: Optional[ManualOverrides] = Field(
        default=None,
        description=(
            "Optional caller/lender-provided assumptions used only "
            "when verified scheme data is unavailable."
        ),
    )


class IntegrationResponse(BaseModel):
    """
    Response returned by the integration layer.
    """

    success: bool

    selected_scheme_code: str

    scheme_match: dict[str, Any]

    financial_summary: Optional[dict[str, Any]] = None

    repayment: dict[str, Any]

    missing_fields: list[str] = Field(default_factory=list)

    used_manual_overrides: list[str] = Field(default_factory=list)

    subsidy_rate: Optional[float] = None

    message: str