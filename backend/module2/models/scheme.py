"""
models/scheme.py

Purpose:
    Defines the data structure for government financial schemes.

    This file ONLY defines the shape of scheme data (Pydantic models).
    It does NOT contain:
        - actual PMMY or PMEGP values (those come later, in a separate
          verified data file)
        - scheme matching / eligibility decision logic
        - API routes
        - database code
        - financial/EMI calculations

Models defined here:
    - LoanCategory:        one loan category/product under a scheme
                            (used by PMMY's Shishu / Kishor / Tarun /
                            Tarun Plus).
    - FinancingCondition:  one conditional financing rule that applies
                            only when specific beneficiary/location/
                            sector/category criteria are met (used by
                            PMEGP, whose contribution/subsidy rates are
                            NOT a single universal number).
    - SchemeRule:          one VERSIONED set of financial rules for a
                            scheme, holding both loan_categories (PMMY)
                            and financing_conditions (PMEGP) as lists.
    - Scheme:              the scheme's stable identity (name, type,
                            description, target beneficiary) plus the
                            list of SchemeRule versions that have
                            applied to it.

Why FinancingCondition exists:
    PMEGP's beneficiary contribution and margin-money subsidy are NOT
    single fixed numbers -- they depend on the beneficiary's category
    (general/special), location (rural/urban), and business sector
    (manufacturing/business-service). A single beneficiary_contribution_
    rate or subsidy_rate field on SchemeRule cannot represent this.
    FinancingCondition lets a SchemeRule hold a LIST of these
    combinations instead, without inventing a separate PMEGP-only model.

Why LoanCategory still exists separately from FinancingCondition:
    PMMY's structure is a different shape of variation -- it varies by
    loan tier (Shishu/Kishor/Tarun/Tarun Plus) with its own loan-amount
    range, NOT by beneficiary category/location/sector. Interest rate
    and tenure are deliberately NOT part of LoanCategory, because PMMY's
    interest rate is set by the lending bank, not the government scheme
    itself -- inventing a rate here would misrepresent how PMMY works.

Future direction (not implemented here):
    A later service function such as
        get_applicable_financing_condition(scheme, beneficiary_category,
                                            location_type, business_sector,
                                            loan_category)
    will pick the right FinancingCondition (or LoanCategory) for a given
    user. This file only provides the data shape that function will read
    from -- no matching logic lives here.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class LoanCategory(BaseModel):
    """
    One loan category/product under a scheme.

    Example use: PMMY's Shishu / Kishor / Tarun / Tarun Plus categories,
    each with its own loan-amount range.

    IMPORTANT: No actual PMMY monetary values are set here. This is only
    the structure. Real values are added later in a separate, clearly
    labelled seed data file, verified against an official source.

    Interest rate and tenure are deliberately NOT included here: PMMY's
    interest rate is determined by the lending bank/institution, not
    fixed by the scheme, so inventing one would misrepresent PMMY.
    """

    category_name: str = Field(
        ...,
        description="Name of the loan category, e.g. 'Shishu', 'Kishor', "
                    "'Tarun', 'Tarun Plus'.",
    )
    minimum_loan_amount: Optional[float] = Field(
        default=None,
        ge=0,
        description="Minimum loan amount for this category, if specified.",
    )
    maximum_loan_amount: float = Field(
        ...,
        gt=0,
        description="Maximum loan amount for this category.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Plain-language description of who this category suits, "
                    "e.g. 'For very small/starting businesses'.",
    )

    @model_validator(mode="after")
    def check_min_not_greater_than_max(self) -> "LoanCategory":
        if (
            self.minimum_loan_amount is not None
            and self.minimum_loan_amount > self.maximum_loan_amount
        ):
            raise ValueError(
                f"LoanCategory '{self.category_name}': minimum_loan_amount "
                "cannot be greater than maximum_loan_amount."
            )
        return self


class FinancingCondition(BaseModel):
    """
    One conditional financing rule within a SchemeRule.

    Example use: PMEGP's beneficiary contribution and subsidy rates,
    which differ depending on beneficiary category (general/special),
    location (rural/urban), and business sector (manufacturing/
    business-service). A SchemeRule can hold a LIST of these to cover
    every applicable combination, instead of one universal rate.

    All condition fields (beneficiary_category, location_type,
    business_sector, loan_category) are optional: a condition may match
    on any subset of them, and matching logic itself is implemented
    later, not in this file.

    IMPORTANT: No actual PMEGP values are set here. This is only the
    structure. Real values are added later in a separate, clearly
    labelled seed data file, verified against an official source.
    """

    condition_code: str = Field(
        ...,
        description="Short unique code for this condition, e.g. "
                    "'PMEGP_GENERAL_RURAL_MFG'.",
    )
    description: str = Field(
        ...,
        description="Plain-language description of when this condition applies.",
    )

    # --- What this condition matches on (all optional; matching logic is elsewhere) ---
    beneficiary_category: Optional[str] = Field(
        default=None,
        description="Beneficiary category this condition applies to, e.g. "
                    "'general', 'special' (SC/ST/OBC/women/etc., as officially defined).",
    )
    location_type: Optional[str] = Field(
        default=None,
        description="Location type this condition applies to, e.g. 'rural', 'urban'.",
    )
    business_sector: Optional[str] = Field(
        default=None,
        description="Business sector this condition applies to, e.g. "
                    "'manufacturing', 'business_service'.",
    )
    loan_category: Optional[str] = Field(
        default=None,
        description="Loan category this condition applies to, if relevant "
                    "(links to a LoanCategory.category_name).",
    )

    # --- What this condition sets (all optional; not every condition sets every value) ---
    beneficiary_contribution_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Beneficiary contribution under this condition, as a "
                    "FRACTION (e.g. 0.05 for 5%).",
    )
    bank_financing_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Bank loan financing under this condition, as a FRACTION.",
    )
    subsidy_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Government margin-money subsidy under this condition, "
                    "as a FRACTION. This is a grant, NOT a loan.",
    )
    maximum_project_cost: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum project cost under this condition, if it differs "
                    "from the scheme-wide limit (e.g. manufacturing vs "
                    "business/service sector limits differ under PMEGP).",
    )
    maximum_loan_amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum loan amount under this condition, if it differs "
                    "from the scheme-wide limit.",
    )

    # Note: contribution + bank_financing + subsidy are deliberately NOT
    # validated to sum to 1. PMEGP's subsidy is a credit-linked
    # margin-money subsidy, not a simple universal financing percentage,
    # so enforcing that sum would misrepresent how it actually works.


class SchemeRule(BaseModel):
    """
    One VERSIONED set of financial rules for a government scheme.

    A single Scheme may have multiple SchemeRule entries over its
    lifetime -- one per period during which a particular set of numbers
    (contribution rate, interest rate, limits, etc.) was in effect.

    Two different kinds of variation are supported side by side:
        - loan_categories:      PMMY-style variation by loan tier.
        - financing_conditions: PMEGP-style variation by beneficiary
                                 category / location / sector.
    A scheme uses whichever list applies to it; the other stays empty.

    IMPORTANT: No actual government values are set here. This is only
    the structure. Real values are added later in a separate, clearly
    labelled seed data file, and must be verified against an official
    source before use.
    """

    scheme_code: str = Field(
        ...,
        description="Code of the scheme this rule belongs to (e.g. 'PMMY', 'PMEGP').",
    )

    # --- Project cost boundaries (scheme-wide; may be overridden per-condition) ---
    minimum_project_cost: Optional[float] = Field(
        default=None,
        gt=0,
        description="Minimum project cost this scheme will finance, if specified.",
    )
    maximum_project_cost: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum project cost this scheme will finance, if specified. "
                    "May be overridden per-condition (e.g. differs by sector).",
    )

    # --- Direct loan limit (scheme-wide; may be overridden per-condition/category) ---
    maximum_loan_amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum loan amount for this rule, if the scheme does "
                    "not split limits across loan_categories or financing_conditions.",
    )

    # --- Scheme-wide contribution / financing / subsidy (may be overridden per-condition) ---
    beneficiary_contribution_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Beneficiary's required contribution, as a FRACTION "
                    "(e.g. 0.10 for 10%), if a single scheme-wide rate applies. "
                    "For PMEGP, prefer financing_conditions instead, since the "
                    "actual rate varies by beneficiary category/location/sector.",
    )
    bank_financing_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Portion of the project financed via a bank loan, as a "
                    "FRACTION, if a single scheme-wide rate applies.",
    )
    subsidy_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Government margin-money subsidy rate, as a FRACTION, "
                    "if a single scheme-wide rate applies. This is a grant, "
                    "NOT a loan.",
    )
    maximum_subsidy_amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Absolute cap on the subsidy amount, if the scheme sets one.",
    )

    # --- Loan terms ---
    annual_interest_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Annual interest rate as a PERCENTAGE (e.g. 8.0 for 8%), "
                    "not a fraction. Must remain Optional and unset for PMMY: "
                    "PMMY's interest rate is set by the lending institution, "
                    "not fixed by the scheme itself.",
    )
    tenure_months: Optional[int] = Field(
        default=None,
        gt=0,
        le=600,
        description="Loan tenure in months, if a single tenure applies to "
                    "this rule as a whole. Must remain unset for PMMY, since "
                    "tenure is determined by the lending institution.",
    )
    moratorium_months: Optional[int] = Field(
        default=None,
        ge=0,
        description="Moratorium (repayment holiday) period in months, if any.",
    )

    # --- PMMY-style multiple loan categories (empty list if not applicable) ---
    loan_categories: List[LoanCategory] = Field(
        default_factory=list,
        description="Loan categories under this rule, e.g. PMMY's Shishu / "
                    "Kishor / Tarun / Tarun Plus. Empty for schemes that "
                    "don't split into tiers (e.g. PMEGP).",
    )

    # --- PMEGP-style conditional financing rules (empty list if not applicable) ---
    financing_conditions: List[FinancingCondition] = Field(
        default_factory=list,
        description="Conditional financing rules under this rule, e.g. "
                    "PMEGP's contribution/subsidy rates varying by "
                    "beneficiary category, location, and business sector. "
                    "Empty for schemes with a single scheme-wide rate "
                    "(e.g. PMMY, which uses loan_categories instead).",
    )

    # --- Eligibility (kept as simple readable text for MVP) ---
    eligibility_conditions: List[str] = Field(
        default_factory=list,
        description="Plain-language eligibility conditions for this rule "
                    "version, e.g. 'Applicant age between 18 and 45'. "
                    "Kept as simple text for the MVP; may become structured "
                    "logic in the final project.",
    )

    # --- Source attribution & versioning ---
    source_name: str = Field(
        ...,
        description="Name of the official source, e.g. 'Ministry of MSME'.",
    )
    source_url: Optional[str] = Field(
        default=None,
        description="URL of the official document/page this rule was taken from.",
    )
    effective_from: date = Field(
        ...,
        description="Date from which this rule version applies.",
    )
    effective_to: Optional[date] = Field(
        default=None,
        description="Date this rule version stopped applying, if it has ended. "
                    "None means it is still in effect.",
    )
    version: str = Field(
        ...,
        description="Version label for this rule, e.g. 'v1', '2025-26'.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this rule version is the one currently in use "
                    "by the application. Older versions should be kept with "
                    "is_active=False rather than deleted.",
    )

    @model_validator(mode="after")
    def check_project_cost_bounds(self) -> "SchemeRule":
        if (
            self.minimum_project_cost is not None
            and self.maximum_project_cost is not None
            and self.minimum_project_cost > self.maximum_project_cost
        ):
            raise ValueError(
                "minimum_project_cost cannot be greater than maximum_project_cost."
            )
        return self

    @model_validator(mode="after")
    def check_effective_dates(self) -> "SchemeRule":
        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError("effective_to cannot be earlier than effective_from.")
        return self

    # NOTE: Deliberately NOT validating that beneficiary_contribution_rate +
    # bank_financing_rate + subsidy_rate == 1 (or <= 1). PMEGP's subsidy is
    # a credit-linked margin-money subsidy, not a simple universal financing
    # percentage, so such a check would misrepresent how it actually works.


class Scheme(BaseModel):
    """
    The complete definition of a government financial scheme.

    Holds stable identity information (name, type, description, target
    beneficiary) plus the list of SchemeRule versions that have applied
    to this scheme over time. No version-specific financial numbers live
    directly on this model -- those belong in SchemeRule (and, within
    it, LoanCategory / FinancingCondition).
    """

    scheme_code: str = Field(
        ...,
        description="Unique short code identifying this scheme, e.g. 'PMMY', 'PMEGP'.",
    )
    scheme_name: str = Field(
        ...,
        description="Full official name of the scheme.",
    )
    scheme_type: str = Field(
        ...,
        description="Type/nature of the scheme, e.g. 'Micro Loan', "
                    "'Employment Generation Programme'.",
    )
    description: str = Field(
        ...,
        description="Plain-language description of what the scheme is for.",
    )
    target_beneficiary: str = Field(
        ...,
        description="Who this scheme is meant for, e.g. 'Rural micro-entrepreneurs'.",
    )

    rules: List[SchemeRule] = Field(
        default_factory=list,
        description="All rule versions that have applied to this scheme, "
                    "ordered oldest to newest. Use the entry with "
                    "is_active=True as the current rule. Historical rule "
                    "selection logic is not implemented yet -- this list "
                    "just needs to be able to hold more than one entry "
                    "over time.",
    )

    @model_validator(mode="after")
    def check_rules_belong_to_this_scheme(self) -> "Scheme":
        for rule in self.rules:
            if rule.scheme_code != self.scheme_code:
                raise ValueError(
                    f"SchemeRule with scheme_code='{rule.scheme_code}' does not "
                    f"match parent Scheme's scheme_code='{self.scheme_code}'."
                )
        return self