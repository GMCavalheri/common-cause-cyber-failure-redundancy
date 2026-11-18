# Course: common-cause cyber failure in redundant architectures

Eight lessons, in order, that take a reader from the classical reliability calculation of a
redundant system to a quantified correction for shared cyber vulnerabilities, and to the design
decisions it changes. Each lesson has learning objectives, the theory with derivations, a code
walkthrough, a worked example, exercises with solutions and references, and an executed notebook.
Every number comes from [`validation/results/`](../../validation/results/).

**Prerequisites:** basic probability (independence, the exponential distribution) and Python.
Reliability block diagrams are introduced from scratch in Lesson 1.

| # | lesson | key ideas | the finding | notebook |
|---|---|---|---|---|
| 1 | [The independence assumption](01-the-independence-assumption.md) | structure functions, k-of-n, pivotal decomposition, binary decision diagrams, minimal cut sets | the single mission computer carries 99 % of the baseline's unreliability; a second one is claimed to cut it 99-fold | [01](../../notebooks/01_the_independence_assumption.ipynb) |
| 2 | [When one cause breaks two channels](02-when-one-cause-breaks-two-channels.md) | root causes and coupling factors, basic parameter, beta, MGL and alpha-factor models, the floor | identical redundancy cannot go below $1 - e^{-\beta\lambda t}$; the second computer's 99× becomes 8× | [02](../../notebooks/02_when_one_cause_breaks_two_channels.ipynb) |
| 3 | [The cyber beta factor](03-the-cyber-beta-factor.md) | shared vulnerabilities as coupling factors, thinned Poisson rates, $1-\beta = (1-\beta_p)(1-\beta_c)$, diversity never hurts | the second computer buys 2.2×; cyber events carry 83 % of the order-one cut sets | [03](../../notebooks/03_the_cyber_beta_factor.ipynb) |
| 4 | [Buying independence](04-buying-independence.md) | design spaces, Pareto fronts, value per cost, robust versus fragile conclusions | with any exposure, segmentation is the best buy and a third identical unit the worst | [04](../../notebooks/04_buying_independence.ipynb) |
| 5 | [Redundancy as claimed vs as it is](05-redundancy-as-claimed-vs-as-it-is.md) | three views of one design, tornado analysis, minimax recommendation | redundancy buys 2.74 orders as claimed, 0.88 with cyber CCF; diversity restores 1.65 | [05](../../notebooks/05_redundancy_as_claimed_vs_as_it_is.ipynb) |
| 6 | [Time, repair and a simulation that checks the algebra](06-time-repair-and-a-simulation-that-checks-the-algebra.md) | Markov chains over component states, availability and MTBF, matrix exponential, Monte Carlo with honest intervals | the redundant design's MTBF falls 121-fold; every exact engine is confirmed by simulation | [06](../../notebooks/06_time_repair_and_a_simulation_that_checks_the_algebra.ipynb) |
| 7 | [From a security posture to a number](07-from-a-security-posture-to-a-number.md) | the NIST SP 800-82r3 OT overlay, a rubric to an interval, monotone propagation | posture moves the interval down but cannot remove sharing; SC-29 is in no baseline | [07](../../notebooks/07_from_a_security_posture_to_a_number.ipynb) |
| 8 | [What is (and isn't) new](08-what-is-and-isnt-new.md) | four neighbouring literatures, four kinds of claim, a novelty statement and its search plan | the closest prior work is INL's modified beta for software CCF; the claim is narrow on purpose | [08](../../notebooks/08_what_is_and_isnt_new.ipynb) |

The formal model and its proofs are in [`docs/derivation.md`](../derivation.md); the case-study
report is [`docs/report.md`](../report.md); the boundaries of what is modelled are in
[`docs/scope.md`](../scope.md).

## Suggested paths

* **Reliability engineer, short on time:** Lessons 2, 3 and 5, then the report.
* **Security engineer:** Lessons 1, 3 and 7.
* **Researcher:** the derivation, Lessons 3, 4 and 8, then the related-work note.
