import json
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "schemes.json"


def load_schemes() -> list[dict[str, Any]]:
    """Load verified scheme rules from schemes.json."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize(value: str | None) -> str | None:
    """Normalize text for reliable matching."""
    if value is None:
        return None

    return value.strip().lower().replace("-", "_").replace(" ", "_")


def get_scheme_by_code(scheme_code: str) -> dict[str, Any] | None:
    """Find a scheme by its scheme code."""
    schemes = load_schemes()

    for scheme in schemes:
        if scheme.get("scheme_code") == scheme_code.upper():
            return scheme

    return None


def match_pmmy(
    requested_loan_amount: float,
    tarun_plus_eligible: bool = False,
) -> dict[str, Any] | None:
    """
    Match the requested loan amount with the correct PMMY category.
    """

    scheme = get_scheme_by_code("PMMY")

    if not scheme:
        return None

    rule = scheme["rules"][0]
    categories = rule.get("loan_categories", [])

    for category in categories:
        category_name = category["category_name"]

        # Tarun Plus has an additional eligibility condition.
        if category_name == "Tarun Plus" and not tarun_plus_eligible:
            continue

        minimum = category["minimum_loan_amount"]
        maximum = category["maximum_loan_amount"]

        if minimum <= requested_loan_amount <= maximum:
            return {
                "scheme_code": scheme["scheme_code"],
                "scheme_name": scheme["scheme_name"],
                "match": True,
                "category": category_name,
                "requested_loan_amount": requested_loan_amount,
                "maximum_loan_amount": maximum,
                "interest_rate": rule.get("annual_interest_rate"),
                "tenure_months": rule.get("tenure_months"),
                "contribution_rate": rule.get(
                    "beneficiary_contribution_rate"
                ),
                "subsidy_rate": rule.get("subsidy_rate"),
                "message": category["description"],
            }

    return None


def match_pmegp(
    requested_loan_amount: float,
    beneficiary_category: str,
    location_type: str,
    business_sector: str,
) -> dict[str, Any] | None:
    """
    Match PMEGP using:

    1. Requested loan amount
    2. Beneficiary category
    3. Location type
    4. Business sector

    PMEGP's maximum project-cost limit is converted into the
    maximum possible bank-financed loan using the applicable
    bank-financing rate.
    """

    scheme = get_scheme_by_code("PMEGP")

    if not scheme:
        return None

    rule = scheme["rules"][0]
    conditions = rule.get("financing_conditions", [])

    beneficiary_category = normalize(beneficiary_category)
    location_type = normalize(location_type)
    business_sector = normalize(business_sector)

    category_condition = None
    sector_condition = None

    # ---------------------------------------------------------
    # Find beneficiary + location financing condition
    # ---------------------------------------------------------
    for condition in conditions:
        condition_category = normalize(
            condition.get("beneficiary_category")
        )
        condition_location = normalize(
            condition.get("location_type")
        )

        if (
            condition_category == beneficiary_category
            and condition_location == location_type
        ):
            category_condition = condition
            break

    # ---------------------------------------------------------
    # Find business-sector condition
    # ---------------------------------------------------------
    for condition in conditions:
        condition_sector = normalize(
            condition.get("business_sector")
        )

        if condition_sector == business_sector:
            sector_condition = condition
            break

    # Both conditions are required.
    if not category_condition or not sector_condition:
        return None

    contribution_rate = category_condition.get(
        "beneficiary_contribution_rate"
    )

    bank_financing_rate = category_condition.get(
        "bank_financing_rate"
    )

    subsidy_rate = category_condition.get("subsidy_rate")

    project_cost_limit = sector_condition.get(
        "maximum_project_cost"
    )

    # We cannot determine amount eligibility without these values.
    if (
        contribution_rate is None
        or bank_financing_rate is None
        or project_cost_limit is None
    ):
        return None

    # ---------------------------------------------------------
    # Convert PMEGP project-cost ceiling into maximum loan
    # ---------------------------------------------------------
    maximum_loan_amount = (
        project_cost_limit * bank_financing_rate
    )

    # ---------------------------------------------------------
    # IMPORTANT:
    # Requested loan must fit within the scheme's
    # financing capacity.
    # ---------------------------------------------------------
    if requested_loan_amount > maximum_loan_amount:
        return None

    return {
        "scheme_code": scheme["scheme_code"],
        "scheme_name": scheme["scheme_name"],
        "match": True,
        "beneficiary_category": beneficiary_category,
        "location_type": location_type,
        "business_sector": business_sector,
        "requested_loan_amount": requested_loan_amount,
        "contribution_rate": contribution_rate,
        "bank_financing_rate": bank_financing_rate,
        "subsidy_rate": subsidy_rate,
        "maximum_project_cost": project_cost_limit,
        "maximum_loan_amount": maximum_loan_amount,
        "interest_rate": rule.get("annual_interest_rate"),
        "tenure_months": rule.get("tenure_months"),
        "message": (
            "PMEGP matched based on requested loan amount, "
            "beneficiary category, location and business sector."
        ),
    }


def match_schemes(
    requested_loan_amount: float,
    beneficiary_category: str,
    location_type: str,
    business_sector: str,
    tarun_plus_eligible: bool = False,
) -> dict[str, Any]:
    """
    Dynamically match the user's requested loan amount
    against the currently implemented government schemes.
    """

    matches = []

    # ---------------------------------------------------------
    # PMMY
    # ---------------------------------------------------------
    pmmy_match = match_pmmy(
        requested_loan_amount=requested_loan_amount,
        tarun_plus_eligible=tarun_plus_eligible,
    )

    if pmmy_match:
        matches.append(pmmy_match)

    # ---------------------------------------------------------
    # PMEGP
    # ---------------------------------------------------------
    pmegp_match = match_pmegp(
        requested_loan_amount=requested_loan_amount,
        beneficiary_category=beneficiary_category,
        location_type=location_type,
        business_sector=business_sector,
    )

    if pmegp_match:
        matches.append(pmegp_match)

    return {
        "success": True,
        "requested_loan_amount": requested_loan_amount,
        "total_matches": len(matches),
        "matches": matches,
    }