# Restaurant Pricing Decision Simulator

A competition-ready educational prototype that helps a restaurant commercial manager compare pricing scenarios for a selected store and product.

**Important:** the bundled data is synthetic. The demand elasticity is an explicit assumption, not a model trained on real restaurant transactions. Outputs are scenario calculations, not validated causal forecasts.

## Why this design

The public Illuminati Consulting use-case library lists an "Intelligent Pricing & Promotion Optimization" use case for a leading Quick Service Restaurant chain, alongside demand-driven forecasting and sales-planning decision support. This repository adapts that general business pattern: turn pricing data into a transparent decision, compare financial outcomes, and validate assumptions before rollout. It does not reproduce any proprietary implementation or claim access to client data.

Reference: https://www.illuminaticonsulting.ai/explore

## Features

- Select a synthetic store and product.
- Adjust proposed list price, discount and assumed own-price elasticity.
- Compare baseline, proposed, -5% and +5% scenarios.
- Calculate effective price, expected units, net sales, variable costs, contribution and contribution margin.
- Apply a minimum contribution-margin guardrail.
- Show contribution and price-sensitivity charts.
- Calculate units required to match baseline contribution.
- Export scenario comparisons to CSV.
- Inspect data provenance, methodology and limitations in the app.
- Run unit tests for core calculation logic.

## Quick start

Requires Python 3.10 or newer.

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd restaurant-pricing-decision-simulator
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux**
```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app should open in your browser at the local URL printed by Streamlit.

## Run tests

```bash
pytest -q
```

Only describe tests as passing after running them in your environment.

## Data

`data/synthetic_sales.csv` contains 120 days × 4 stores × 3 products = 1,440 synthetic store-product-day rows. Regenerate it with `python data/generate_sample_data.py`. Names, prices, costs, competitor prices, discounts and orders are invented solely for demonstration and must not be represented as actual company data.

The data are generated to provide variety for the user journey; they do **not** establish causal price response. The app uses a user-controlled constant-elasticity assumption.

## Core methodology

Effective price:

`effective_price = list_price × (1 − discount_pct / 100)`

Expected units:

`Q1 = Q0 × (P1 / P0)^ε`

Contribution:

`contribution = (effective_price − unit_variable_cost) × expected_units`

The elasticity `ε` is assumed by the user and normally negative. A real deployment should estimate demand response using suitable transaction history or controlled experiments, consider confounders, evaluate on held-out periods, and report uncertainty.

## Scope and limitations

This prototype does not include fixed store costs, taxes, delivery commissions, refunds, capacity constraints, customer lifetime value, price competition reactions, cross-product substitution or actual causal estimation. Contribution is not the same as operating profit. The recommendation selects the highest modeled contribution among the small set of scenarios that satisfy the chosen margin guardrail; it does not prove a global optimum.

Before using recommendations in a real business, replace synthetic data with authorized, quality-checked data; agree business guardrails; validate the model; pilot changes; and monitor contribution, demand, complaints and other customer outcomes.

## Suggested 90-second demo

1. Select a store and product.
2. Point out the synthetic-data notice and baseline economics.
3. Increase the proposed price and show the scenario table and charts update.
4. Change the elasticity assumption and show why demand uncertainty matters.
5. Set a margin guardrail and explain the recommendation.
6. Open methodology/limitations and state that actual demand response must be validated before rollout.

## Repository layout

```text
restaurant-pricing-decision-simulator/
├── app.py
├── pricing_engine.py
├── requirements.txt
├── data/
│   ├── synthetic_sales.csv
│   └── generate_sample_data.py
├── tests/
│   └── test_pricing_engine.py
├── docs/
│   └── MODEL_CARD.md
├── .streamlit/
│   └── config.toml
├── .gitignore
└── README.md
```

## Disclaimer

Educational and competition prototype only. Not a pricing recommendation for a real restaurant chain.
