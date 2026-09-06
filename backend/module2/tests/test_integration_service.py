from models.integration import IntegrationInput
from services.integration_service import evaluate_integration


def test_pmegp_integration_success():
    data = IntegrationInput(
        requested_loan_amount=800000,
        beneficiary_category="general",
        location_type="rural",
        business_sector="manufacturing",
        tarun_plus_eligible=False,
        selected_scheme_code="PMEGP",
        available_margin=100000,
        monthly_revenue=100000,
        monthly_operating_cost=60000,
    )

    result = evaluate_integration(data)

    assert result["success"] is True
    assert result["selected_scheme_code"] == "PMEGP"
    assert result["financial_summary"] is not None
    assert result["financial_summary"]["loan_amount"] > 0
    assert result["repayment"]["operating_surplus"] == 40000


def test_invalid_selected_scheme():
    data = IntegrationInput(
        requested_loan_amount=800000,
        beneficiary_category="general",
        location_type="rural",
        business_sector="manufacturing",
        selected_scheme_code="INVALID",
        available_margin=100000,
        monthly_revenue=100000,
        monthly_operating_cost=60000,
    )

    try:
        evaluate_integration(data)
        assert False, "Expected ValueError for invalid scheme"
    except ValueError:
        assert True


def test_requested_loan_amount_is_respected():
    data = IntegrationInput(
        requested_loan_amount=800000,
        beneficiary_category="general",
        location_type="rural",
        business_sector="manufacturing",
        tarun_plus_eligible=False,
        selected_scheme_code="PMEGP",
        available_margin=100000,
        monthly_revenue=100000,
        monthly_operating_cost=60000,
    )

    result = evaluate_integration(data)

    assert result["success"] is True
    assert result["financial_summary"]["loan_amount"] == 800000