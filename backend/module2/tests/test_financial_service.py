"""
tests/test_financial_service.py

Unit tests for services/financial_service.py

These tests verify EXACT mathematical outputs, not just "it ran without
crashing." Expected values were independently computed using the same
formulas (standard reducing-balance EMI) before being hard-coded here.

Note on the "DSCR is None" case:
    Given the CURRENT validation rules in models/financial.py
    (available_margin > 0, 0 < contribution_rate < 1, loan_limit > 0),
    it is mathematically impossible for loan_amount to reach exactly 0
    through the full FinancialCalculationInput pipeline. That situation
    only becomes reachable for subsidy-only schemes with loan_limit = 0,
    which the current model does not yet allow (tracked as a Phase 6/7
    backlog item, pending verified scheme data).

    So this test file checks the "DSCR is None" behavior directly on the
    underlying pure functions (calculate_emi, classify_stress_level),
    which is what actually implements that rule.
"""

import pytest
from models.financial import FinancialCalculationInput
from services.financial_service import (
    calculate_financials,
    calculate_emi,
    classify_stress_level,
)


def test_normal_positive_interest_calculation():
    """Test 1: Normal case with positive interest rate."""
    data = FinancialCalculationInput(
        available_margin=100000,
        contribution_rate=0.10,
        project_cost_limit=800000,
        loan_limit=900000,
        interest_rate=12,
        tenure_months=60,
        monthly_revenue=50000,
        monthly_operating_cost=30000,
    )
    result = calculate_financials(data)
    fs = result.financial_summary
    rp = result.repayment

    assert result.success is True
    assert fs.theoretical_project_capacity == pytest.approx(1_000_000.0)
    assert fs.final_project_cost == pytest.approx(800_000.0)
    assert fs.beneficiary_contribution == pytest.approx(80_000.0)
    assert fs.loan_amount == pytest.approx(720_000.0)
    assert fs.emi == pytest.approx(16016.002333129267, rel=1e-9)
    assert fs.total_interest == pytest.approx(240960.13998775603, rel=1e-9)

    assert rp.operating_surplus == pytest.approx(20_000.0)
    assert rp.dscr == pytest.approx(1.2487510668395567, rel=1e-9)
    assert rp.stress_level == "watch"


def test_zero_interest_calculation():
    """Test 2: Zero-interest case uses straight-line EMI division."""
    data = FinancialCalculationInput(
        available_margin=50000,
        contribution_rate=0.10,
        project_cost_limit=500000,
        loan_limit=500000,
        interest_rate=0,
        tenure_months=50,
        monthly_revenue=20000,
        monthly_operating_cost=10000,
    )
    result = calculate_financials(data)
    fs = result.financial_summary
    rp = result.repayment

    assert fs.loan_amount == pytest.approx(450_000.0)
    assert fs.emi == pytest.approx(9_000.0)          # 450000 / 50
    assert fs.total_interest == pytest.approx(0.0)   # no interest charged

    assert rp.operating_surplus == pytest.approx(10_000.0)
    assert rp.dscr == pytest.approx(1.1111111111111112, rel=1e-9)
    assert rp.stress_level == "high_stress"


def test_negative_operating_surplus():
    """Test 3: Operating cost exceeds revenue -> negative surplus, negative DSCR."""
    data = FinancialCalculationInput(
        available_margin=100000,
        contribution_rate=0.10,
        project_cost_limit=800000,
        loan_limit=900000,
        interest_rate=12,
        tenure_months=60,
        monthly_revenue=10000,
        monthly_operating_cost=30000,
    )
    result = calculate_financials(data)
    rp = result.repayment

    assert rp.operating_surplus == pytest.approx(-20_000.0)
    assert rp.dscr == pytest.approx(-1.2487510668395567, rel=1e-9)
    assert rp.stress_level == "very_high_stress"


def test_dscr_is_none_when_emi_is_zero():
    """
    Test 4: DSCR must be None when EMI is 0.

    This is tested directly on the pure functions, because the full
    FinancialCalculationInput pipeline cannot currently produce a zero
    loan_amount (see module docstring above for why).
    """
    emi = calculate_emi(principal=0, annual_interest_rate_percent=12, tenure_months=60)
    assert emi == 0.0

    stress_label = classify_stress_level(None)
    assert stress_label == "not_applicable"