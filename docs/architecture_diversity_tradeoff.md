# `architecture_diversity_tradeoff`: cost against reliability

**Lesson:** [4 · Buying independence](lessons/04-buying-independence.md) ·
**Code:** [`src/cyberccf/architecture_diversity_tradeoff/`](../src/cyberccf/architecture_diversity_tradeoff/)

## Model

An `Architecture` fixes the number of EGIs (2-3) and mission computers (1-2) and, per group and
attribute, the number of distinct values. The 315 designs are costed with illustrative relative
costs ([`diversity_costs.csv`](../src/cyberccf/data/diversity_costs.csv)) and quantified
exactly; `unreliability_at_scale` re-evaluates a design at any cyber exposure from the same BDD.
`pareto_front` keeps the non-dominated (cost, unreliability) points and `best_within_budget`
picks one.

## Assumptions

Costs are illustrative; only their order (segmentation cheap, dissimilar software dear) is
argued, from the N-version programming literature.

## Verification

The Pareto front against brute force (Hypothesis); refining any attribute never increases
unreliability over the design space; at zero exposure every diversity level equals the physical
model; rescaling equals rebuilding the model.
