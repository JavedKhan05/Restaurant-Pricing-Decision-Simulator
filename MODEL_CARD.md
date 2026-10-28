# Model Card: Restaurant Pricing Decision Simulator

## Intended use
Demonstrate how a restaurant commercial manager can compare illustrative pricing scenarios and understand the trade-off between unit margin and modeled demand.

## Not intended for
Automatic production pricing, causal demand claims, guaranteed financial returns, or chain-wide price deployment without validation.

## Data
The bundled CSV is fully synthetic. It is not sourced from a real restaurant or an actual competitor-price feed. It is included to exercise the interface and calculations.

## Model
Constant-elasticity scenario equation:
`Q1 = Q0 × (P1/P0)^ε`

The elasticity is selected by the user. It is not fitted from the synthetic dataset. The app treats scenario outputs as conditional calculations, not as evidence of actual customer behavior.

## Primary output
Modeled contribution:
`(effective price − unit variable cost) × expected units`

The recommendation picks the highest modeled contribution among a limited candidate set that passes the minimum contribution-margin guardrail.

## Key limitations
- No causal inference.
- No confidence intervals or calibrated probability.
- No stockout, capacity, cross-product substitution or competitor reaction model.
- No fixed store costs, tax, delivery fees, refunds or customer lifetime value.
- No actual data validation beyond basic schema and numeric checks.
- No proof of global optimality.

## Risks and mitigations
- **False precision:** label synthetic data and assumed elasticity visibly.
- **Revenue/profit confusion:** display contribution and explicitly exclude fixed costs.
- **Overgeneralization:** make store and product selectable; still treat results as illustrative.
- **Unsafe rollout:** recommend controlled pilot and human approval.
- **Model misspecification:** validate against authorized real data and controlled tests before production use.

## Required validation before real deployment
1. Data quality and provenance review.
2. Demand estimation strategy and confounder assessment.
3. Held-out temporal validation or controlled experiment.
4. Sensitivity and downside analysis.
5. Business-approved price/margin/customer guardrails.
6. Pilot monitoring and rollback plan.
