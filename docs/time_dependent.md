# `time_dependent`: availability, MTBF and Monte Carlo oracles

**Lesson:** [6 · Time, repair and a simulation that checks the algebra](lessons/06-time-repair-and-a-simulation-that-checks-the-algebra.md) ·
**Code:** [`src/cyberccf/time_dependent/`](../src/cyberccf/time_dependent/)

## Model

A continuous-time Markov chain over failed-component sets ($2^n$ states, $n \le 12$): every
basic event fails the working components it covers at its rate; every failed component is
repaired at $1/\text{MTTR}$ on its own clock. `steady_state` gives availability, failure
frequency, MTBF ($A/\omega$) and MDT ($(1-A)/\omega$); `transient_unreliability` gives mission
unreliability from $e^{Gt}$ with no repair; `one_of_two_markov` is the closed form for a pair.

`simulate_missions` (vectorised, Wilson interval) and `simulate_availability` (discrete-event,
independent replications, Student-t interval) share nothing with the exact engines but the
model description.

## Assumptions

Exponential repair, one repair resource per component, independent repair after a common-cause
event (a coordinated cyber recovery would lengthen down time).

## Verification

The 1-of-2 closed form; CPS-01's steady state reproduced exactly for the independence case;
$e^{Gt}$ equal to the BDD on every navigation variant; both simulations covering the exact
values within 99.7 % intervals.
