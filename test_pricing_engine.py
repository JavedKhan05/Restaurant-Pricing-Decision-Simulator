import pytest
from pricing_engine import (
    effective_price, forecast_units, calculate_scenario, break_even_units,
    recommend_scenario
)


def test_effective_price_applies_discount_once():
    assert effective_price(200, 10) == pytest.approx(180)


def test_baseline_scenario_matches_baseline_contribution_when_no_discount_and_same_price():
    result = calculate_scenario(
        "baseline", 200, 0, 100, 1000, 200, 100000, -1.2
    )
    assert result.expected_units == pytest.approx(1000)
    assert result.contribution == pytest.approx(100000)


def test_price_increase_reduces_units_for_negative_elasticity():
    assert forecast_units(1000, 200, 220, -1.2) < 1000


def test_zero_elasticity_keeps_units_constant():
    assert forecast_units(1000, 200, 220, 0) == pytest.approx(1000)


def test_zero_baseline_units_stays_zero():
    assert forecast_units(0, 200, 220, -1.2) == 0


def test_break_even_units_returns_none_when_unit_contribution_nonpositive():
    assert break_even_units(100000, 90, 100) is None


def test_break_even_units_calculation():
    assert break_even_units(100000, 200, 100) == pytest.approx(1000)


def test_invalid_discount_rejected():
    with pytest.raises(ValueError):
        effective_price(200, 100)


def test_positive_elasticity_rejected():
    with pytest.raises(ValueError):
        forecast_units(1000, 200, 220, 0.5)


def test_recommendation_maximizes_contribution_within_margin_constraint():
    results = [
        calculate_scenario("A", 200, 0, 100, 1000, 200, 100000, -1.2),
        calculate_scenario("B", 220, 0, 100, 1000, 200, 100000, -1.2),
    ]
    best, _ = recommend_scenario(results, min_margin_pct=20)
    assert best is not None
    assert best.contribution == max(r.contribution for r in results if r.contribution_margin_pct >= 20)
