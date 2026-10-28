"""Transparent pricing calculations for the Restaurant Pricing Decision Simulator."""
from dataclasses import dataclass
from typing import Iterable
import math
import pandas as pd


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    list_price: float
    discount_pct: float
    effective_price: float
    expected_units: float
    net_sales: float
    variable_cost: float
    contribution: float
    contribution_margin_pct: float
    change_vs_baseline: float
    change_vs_baseline_pct: float


def validate_inputs(list_price, discount_pct, unit_cost, baseline_units, elasticity):
    values = [list_price, discount_pct, unit_cost, baseline_units, elasticity]
    if any(v is None or not math.isfinite(float(v)) for v in values):
        raise ValueError("All inputs must be finite numbers.")
    if list_price <= 0:
        raise ValueError("List price must be greater than zero.")
    if not 0 <= discount_pct < 100:
        raise ValueError("Discount must be between 0% (inclusive) and 100% (exclusive).")
    if unit_cost < 0:
        raise ValueError("Unit variable cost cannot be negative.")
    if baseline_units < 0:
        raise ValueError("Baseline units cannot be negative.")
    if elasticity > 0:
        raise ValueError("Own-price elasticity should be zero or negative in this model.")
    if elasticity < -5:
        raise ValueError("Elasticity below -5 is outside this prototype's configured guardrail.")
    return True


def effective_price(list_price: float, discount_pct: float) -> float:
    if list_price <= 0:
        raise ValueError("List price must be greater than zero.")
    if not 0 <= discount_pct < 100:
        raise ValueError("Discount must be between 0% and 100% (exclusive of 100%).")
    return float(list_price) * (1 - float(discount_pct) / 100)


def forecast_units(baseline_units: float, baseline_effective_price: float,
                   scenario_effective_price: float, elasticity: float) -> float:
    """Constant-elasticity scenario model; outputs expected units, not a causal forecast."""
    if baseline_units < 0:
        raise ValueError("Baseline units cannot be negative.")
    if baseline_effective_price <= 0 or scenario_effective_price <= 0:
        raise ValueError("Effective prices must be greater than zero.")
    if elasticity > 0 or elasticity < -5:
        raise ValueError("Elasticity must be between -5 and 0 for this prototype.")
    if baseline_units == 0:
        return 0.0
    return float(baseline_units) * (float(scenario_effective_price) / float(baseline_effective_price)) ** float(elasticity)


def calculate_scenario(scenario: str, list_price: float, discount_pct: float,
                       unit_cost: float, baseline_units: float,
                       baseline_effective_price: float, baseline_contribution: float,
                       elasticity: float) -> ScenarioResult:
    validate_inputs(list_price, discount_pct, unit_cost, baseline_units, elasticity)
    p = effective_price(list_price, discount_pct)
    units = forecast_units(baseline_units, baseline_effective_price, p, elasticity)
    sales = p * units
    cost = unit_cost * units
    contribution = sales - cost
    margin = (contribution / sales * 100) if sales > 0 else 0.0
    delta = contribution - baseline_contribution
    delta_pct = (delta / abs(baseline_contribution) * 100) if baseline_contribution != 0 else 0.0
    return ScenarioResult(
        scenario=scenario,
        list_price=float(list_price),
        discount_pct=float(discount_pct),
        effective_price=p,
        expected_units=units,
        net_sales=sales,
        variable_cost=cost,
        contribution=contribution,
        contribution_margin_pct=margin,
        change_vs_baseline=delta,
        change_vs_baseline_pct=delta_pct,
    )


def break_even_units(target_contribution: float, effective_price_value: float,
                     unit_cost: float) -> float | None:
    """Units needed to reach target contribution; None when price does not exceed unit cost."""
    unit_contribution = effective_price_value - unit_cost
    if unit_contribution <= 0:
        return None
    return max(0.0, target_contribution / unit_contribution)


def recommend_scenario(results: Iterable[ScenarioResult], min_margin_pct: float = 0.0) -> tuple[ScenarioResult | None, str]:
    """Maximize contribution among scenarios meeting the margin guardrail."""
    feasible = []
    for r in results:
        if r.contribution_margin_pct + 1e-9 < min_margin_pct:
            continue
        feasible.append(r)
    if not feasible:
        return None, "No scenario satisfies the configured contribution-margin constraint."
    best = max(feasible, key=lambda r: r.contribution)
    return best, "Highest modeled contribution among scenarios that satisfy the configured margin constraint."


def scenario_to_dict(result: ScenarioResult) -> dict:
    return {
        "Scenario": result.scenario,
        "List price (₹)": result.list_price,
        "Discount (%)": result.discount_pct,
        "Effective price (₹)": result.effective_price,
        "Expected units": result.expected_units,
        "Net sales (₹)": result.net_sales,
        "Variable cost (₹)": result.variable_cost,
        "Contribution (₹)": result.contribution,
        "Contribution margin (%)": result.contribution_margin_pct,
        "Change vs baseline (₹)": result.change_vs_baseline,
        "Change vs baseline (%)": result.change_vs_baseline_pct,
    }


def load_and_validate_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "date", "store_id", "store_name", "product_id", "product_name",
        "list_price", "discount_pct", "units_sold", "unit_variable_cost",
        "competitor_price", "promotion_flag", "data_type"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("Dataset is empty.")
    if (df["list_price"] <= 0).any():
        raise ValueError("Dataset contains non-positive list prices.")
    if ((df["discount_pct"] < 0) | (df["discount_pct"] >= 100)).any():
        raise ValueError("Dataset contains invalid discount percentages.")
    if (df["units_sold"] < 0).any() or (df["unit_variable_cost"] < 0).any():
        raise ValueError("Dataset contains negative units or variable costs.")
    return df
