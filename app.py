from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from pricing_engine import (
    calculate_scenario, break_even_units, load_and_validate_data,
    recommend_scenario, scenario_to_dict
)

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "synthetic_sales.csv"

st.set_page_config(page_title="Restaurant Pricing Decision Simulator", page_icon="🍽️", layout="wide")
st.title("Restaurant Pricing Decision Simulator")
st.caption("A transparent decision-support prototype • Synthetic demonstration data • Not a validated causal pricing model")

with st.sidebar:
    st.header("Decision inputs")
    st.write("Choose a store and product, then compare price scenarios.")
    data_path = DATA_PATH

try:
    data = load_and_validate_data(str(data_path))
except Exception as exc:
    st.error(f"Could not load the sample dataset: {exc}")
    st.stop()

store_options = data[["store_id", "store_name"]].drop_duplicates().sort_values("store_name")
selected_store_name = st.sidebar.selectbox("Store", store_options["store_name"].tolist())
selected_store_id = store_options.loc[store_options["store_name"] == selected_store_name, "store_id"].iloc[0]
store_df = data[data["store_id"] == selected_store_id]
product_options = store_df[["product_id", "product_name"]].drop_duplicates().sort_values("product_name")
selected_product_name = st.sidebar.selectbox("Product", product_options["product_name"].tolist())
selected_product_id = product_options.loc[product_options["product_name"] == selected_product_name, "product_id"].iloc[0]
hist = store_df[store_df["product_id"] == selected_product_id].copy()
hist["effective_price"] = hist["list_price"] * (1 - hist["discount_pct"] / 100)

default_list_price = float(hist["list_price"].median())
unit_cost = float(hist["unit_variable_cost"].median())
baseline_effective_price = float(hist["effective_price"].mean())
baseline_units = float(hist["units_sold"].mean())
baseline_contribution = float((baseline_effective_price - unit_cost) * baseline_units)
baseline_margin = ((baseline_contribution / (baseline_effective_price * baseline_units)) * 100) if baseline_effective_price * baseline_units > 0 else 0

st.info("The bundled dataset is synthetic and exists only to demonstrate the workflow. Forecast outputs are scenario estimates driven by an assumed elasticity; they are not evidence of actual customer response.")

left, right = st.columns([1.05, 1.5], gap="large")
with left:
    st.subheader("1. Set the proposed price")
    st.metric("Baseline effective price", f"₹{baseline_effective_price:,.2f}")
    st.metric("Baseline average units/day", f"{baseline_units:,.1f}")
    st.metric("Modeled baseline contribution/day", f"₹{baseline_contribution:,.0f}")
    proposed_list_price = st.number_input("Proposed list price (₹)", min_value=1.0, max_value=5000.0, value=float(default_list_price), step=5.0)
    discount_pct = st.slider("Proposed discount (%)", min_value=0.0, max_value=50.0, value=0.0, step=1.0)
    elasticity = st.slider("Assumed own-price elasticity", min_value=-5.0, max_value=0.0, value=-1.2, step=0.1,
                           help="Illustrative assumption only. Negative values imply expected demand falls as price rises.")
    min_margin_pct = st.slider("Minimum contribution margin guardrail (%)", min_value=0.0, max_value=80.0, value=20.0, step=1.0)
    st.caption(f"Median unit variable cost used: ₹{unit_cost:,.2f}. Fixed store costs are not included.")

with right:
    st.subheader("2. Compare pricing scenarios")
    scenarios = []
    candidate_inputs = [
        ("Maintain baseline", baseline_effective_price, 0.0),
        ("Proposed", proposed_list_price, discount_pct),
        ("Price -5%", max(1.0, proposed_list_price * 0.95), discount_pct),
        ("Price +5%", min(5000.0, proposed_list_price * 1.05), discount_pct),
    ]
    for name, list_p, disc in candidate_inputs:
        scenarios.append(calculate_scenario(
            scenario=name,
            list_price=float(list_p),
            discount_pct=float(disc),
            unit_cost=unit_cost,
            baseline_units=baseline_units,
            baseline_effective_price=baseline_effective_price,
            baseline_contribution=baseline_contribution,
            elasticity=elasticity,
        ))
    results_df = pd.DataFrame([scenario_to_dict(s) for s in scenarios])
    st.dataframe(
        results_df.style.format({
            "List price (₹)": "₹{:,.2f}",
            "Discount (%)": "{:.1f}%",
            "Effective price (₹)": "₹{:,.2f}",
            "Expected units": "{:,.1f}",
            "Net sales (₹)": "₹{:,.0f}",
            "Variable cost (₹)": "₹{:,.0f}",
            "Contribution (₹)": "₹{:,.0f}",
            "Contribution margin (%)": "{:.1f}%",
            "Change vs baseline (₹)": "₹{:,.0f}",
            "Change vs baseline (%)": "{:+.1f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

feasible = [s for s in scenarios if s.contribution_margin_pct >= min_margin_pct]
best, reason = recommend_scenario(scenarios, min_margin_pct=min_margin_pct)
st.subheader("3. Recommendation")
if best is None:
    st.warning("No scenario meets the configured minimum contribution-margin guardrail. Adjust the price or guardrail, or review cost assumptions.")
else:
    delta_pct = best.change_vs_baseline_pct
    st.success(f"Modeled recommendation: **{best.scenario}** at an effective price of **₹{best.effective_price:,.2f}**.")
    st.write(f"**Why:** {reason} The scenario produces modeled contribution of ₹{best.contribution:,.0f} per average day, a change of ₹{best.change_vs_baseline:,.0f} ({delta_pct:+.1f}%) versus the baseline, while meeting the selected contribution-margin guardrail.")
    st.caption("This is the best result among the four modeled scenarios only—not a proof of the globally optimal price.")
    if best.scenario != "Maintain baseline":
        st.write("**Suggested next step:** run a limited, controlled pilot using actual transaction data before rolling out the change. Monitor contribution, units, customer complaints, refunds and competitor response.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Contribution by scenario")
    fig = px.bar(results_df, x="Scenario", y="Contribution (₹)", title="Modeled contribution per average day", text_auto=".0f")
    fig.update_layout(xaxis_title="", yaxis_title="Contribution (₹)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("Price–demand sensitivity")
    proposed_effective = proposed_list_price * (1 - discount_pct / 100)
    price_grid = [max(1, proposed_effective * x / 100) for x in range(75, 126, 5)]
    sens = []
    for p in price_grid:
        q = baseline_units * (p / baseline_effective_price) ** elasticity if baseline_units > 0 else 0
        c = (p - unit_cost) * q
        sens.append({"Effective price (₹)": p, "Expected units": q, "Contribution (₹)": c})
    sens_df = pd.DataFrame(sens)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sens_df["Effective price (₹)"], y=sens_df["Contribution (₹)"], mode="lines+markers", name="Contribution"))
    fig2.update_layout(title="Contribution across price scenarios", xaxis_title="Effective price (₹)", yaxis_title="Modeled contribution (₹)")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("4. Break-even and assumptions")
proposed_effective = proposed_list_price * (1 - discount_pct / 100)
be_units = break_even_units(baseline_contribution, proposed_effective, unit_cost)
if be_units is None:
    st.warning("At this effective price, unit contribution is zero or negative. The proposed price cannot match baseline contribution at any positive volume.")
else:
    st.write(f"Units needed at the proposed effective price to match baseline contribution: **{be_units:,.1f} units/day**.")
    st.write(f"Modeled units at the proposed price: **{baseline_units * (proposed_effective / baseline_effective_price) ** elasticity:,.1f} units/day**.")

with st.expander("Data provenance, methodology and limitations"):
    st.markdown("""
    **Data provenance:** All bundled store-product-day observations are synthetic and generated for this prototype. Store names, prices, costs, competitor prices, discounts and units are not actual company records or public-market observations.

    **Demand model:** Constant-elasticity scenario equation: `Q1 = Q0 × (P1 / P0)^ε`, where `ε` is an assumed own-price elasticity. The default is illustrative, not empirically estimated.

    **Financial model:** `Contribution = (effective selling price − unit variable cost) × expected units`. Fixed costs, taxes, delivery fees, refunds, capacity limits, customer lifetime value and competitor reactions are not modeled.

    **Key limitation:** The tool illustrates how decisions could be evaluated; it does not establish causal price sensitivity or validate a real-world price recommendation. Before deployment, estimate demand using suitable historical data and/or a controlled experiment, validate on held-out periods, and monitor guardrails.
    """)
st.download_button("Download scenario comparison CSV", data=results_df.to_csv(index=False).encode("utf-8"),
                   file_name="pricing_scenario_comparison.csv", mime="text/csv")
st.caption("Prototype for educational/competition use. Do not deploy prices from this model without business and data validation.")
