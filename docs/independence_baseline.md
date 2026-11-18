# `independence_baseline`: block diagrams, basic events and exact quantification

**Lesson:** [1 · The independence assumption](lessons/01-the-independence-assumption.md) ·
**Code:** [`src/cyberccf/independence_baseline/`](../src/cyberccf/independence_baseline/)

## Model

* A **block diagram** in success logic: `Series`, `Parallel` and `KofN` blocks over component
  names (a block works when at least $k$ children work). A component may appear in several
  places.
* **Basic events** occur as independent Poisson processes of rate $\lambda_e$; over a mission
  of $t$ hours, $q_e = 1 - e^{-\lambda_e t}$. Each component fails when any of its events
  occurs. One event per component is the independence model; an event listed as a cause of
  several components is a common cause (Phases 2-3 reuse the engine unchanged).
* **Exact quantification**: the system's failure function is built once as a reduced ordered
  binary decision diagram over the events (Bryant, 1986) and evaluated by
  $P(\text{node}) = q_e P(\text{high}) + (1 - q_e) P(\text{low})$ (Rauzy, 1993), which is the
  pivotal decomposition with repeated work shared and no cancellation.

## API

| function | purpose |
|---|---|
| `Series`, `Parallel`, `KofN`, `leaves`, `describe`, `at_least_k` | structure |
| `BasicEvent`, `Model`, `independent_model` | events and models |
| `failure_probability(model, q)`, `unreliability(model, hours)` | exact quantification |
| `enumerate_failure_probability` | brute-force oracle (tests) |
| `minimal_cut_sets`, `system_works`, `works_with_failed`, `shared_events` | structure analysis |
| `navigation_model(egi_units, bus_channels, mission_computers=...)` | the CPS-series system |
| closed forms: `series_unreliability`, `parallel_unreliability`, `k_of_n_reliability`, `navigation_unreliability` | oracles |

## Assumptions

Constant failure rates, no repair within a mission, mutually independent basic events. The
parameters ([`system_parameters.csv`](../src/cyberccf/data/system_parameters.csv)) are copied
from CPS-01 with their basis; all are illustrative assumptions.

## Verification

Closed forms; the binomial tail; the BDD against exhaustive truth tables; the engine against
brute-force enumeration on random models with shared events (Hypothesis); and the navigation
system against CPS-01 (`cyberrel`) and CPS-02 (`cpsrbd`) v1.0.0 to $10^{-12}$.
