# Derivation: the beta-factor model extended to shared cyber vulnerabilities

This note states the model of this repository formally and proves the results the lessons
use. It is written as groundwork for a paper, so every claim is either proved here, cited, or
checked numerically by [`validation/reduction_checks.py`](../validation/reduction_checks.py)
(results in [`reduction_checks.md`](../validation/results/reduction_checks.md)). Notation
follows NUREG/CR-5485 where it can.

## 1. Setting

**System.** A coherent system of components $C = \{1, \dots, n\}$ with structure function
$\phi : \{0,1\}^n \to \{0,1\}$ ($x_j = 1$ when component $j$ works; $\phi$ is non-decreasing,
$\phi(0) = 0$, $\phi(1) = 1$). Missions last $t$ hours with no repair.

**Basic events.** A finite set $E$ of basic events. Event $e$ occurs according to a
homogeneous Poisson process of rate $\lambda_e \ge 0$, independently of all other events, so it
occurs during the mission with probability $q_e = 1 - e^{-\lambda_e t}$. Each event has a
non-empty set of components $S_e \subseteq C$ that it fails. Component $j$ fails during the
mission if and only if some event $e$ with $j \in S_e$ occurs:

```math
x_j = \prod_{e \,:\, j \in S_e} (1 - Y_e), \qquad Y_e = \mathbb{1}[e \text{ occurs}].
```

The system fails with probability $Q = P(\phi(x) = 0)$, computed exactly by a binary decision
diagram over the $Y_e$ (Bryant, 1986; Rauzy, 1993).

**Physical part.** Each component $j$ has a physical rate $\lambda_{p,j}$. Components are
partitioned into common-cause component groups $G$ of identical members (equal
$\lambda_{p,j} = \lambda_p$). A parametric model gives fractions $f_k$ with
$\sum_{k=1}^{m} \binom{m-1}{k-1} f_k = 1$ ($m = |G|$), and the group contributes one event of
rate $f_k \lambda_p$ for every subset of $G$ of size $k$ with $f_k > 0$ (NUREG/CR-5485 section
5; beta factor $f_1 = 1-\beta_p$, $f_m = \beta_p$).

**Cyber part.** A finite set of attributes $D$ (here firmware, network, supply chain). Each
programmable component $j$ holds a value $a_j(d)$ of each attribute. For every attribute $d$
and value $v$ held by at least one component there is one event $e_{d,v}$ with

```math
S_{e_{d,v}} = \{ j : a_j(d) = v \}, \qquad \lambda_{e_{d,v}} = \lambda_d = \nu_d\, p_d,
```

where $\nu_d$ is the rate of attempts against one value of $d$ and $p_d$ the probability that
an attempt defeats every holder (Poisson thinning). The rate is **per value**: it does not
depend on how many components hold $v$. Write $\lambda_c = \sum_{d} \lambda_d$ for the cyber
exposure of a programmable component.

**Definitions.** For a component $j$, with $\Lambda_j = \sum_{e \ni j} \lambda_e$ (sum over the events with $j \in S_e$)
its total rate,

```math
\beta_{c,j} = \frac{1}{\Lambda_j} \sum_{\substack{e \text{ cyber} \\ j \in S_e,\ |S_e| \ge 2}} \lambda_e,
\qquad
\beta_j = \frac{1}{\Lambda_j} \sum_{\substack{e \\ j \in S_e,\ |S_e| \ge 2}} \lambda_e .
```

$\beta_{c,j}$ is the **cyber beta factor** and $\beta_j$ the **effective beta factor**: the
shares of the component's failure rate that come from events it shares with another
component, of cyber origin and of any origin.

## 2. Results

### Proposition 1 (reductions)

(a) If $\lambda_d = 0$ for every $d$, the model is the classical physical CCF model.
(b) If moreover every group has $f_1 = 1$, it is the classical independence model.

*Proof.* With zero rate an event never occurs ($q_e = 0$), so it can be removed without
changing the distribution of $x$; the remaining events are exactly those of the physical
model, and with $f_1 = 1$ each component keeps one event of its own. $\square$

### Proposition 2 (marginals are conserved)

Every component's mission failure probability is $1 - e^{-\Lambda_j t}$, where
$\Lambda_j = \lambda_{p,j} + \lambda_c$ for a programmable component and $\lambda_{p,j}$
otherwise, **whatever the CCF fractions and whatever the attribute values**.

*Proof.* Component $j$ survives iff none of its events occurs; by independence this has
probability $\prod_{e \ni j} e^{-\lambda_e t} = e^{-\Lambda_j t}$. Its physical events have
rates summing to $\lambda_p \sum_k \binom{m-1}{k-1} f_k = \lambda_p$, and it holds exactly one
value of each attribute, so its cyber events sum to $\lambda_c$. $\square$

So common cause, physical or cyber, never changes how often a component fails. It changes only
**which components fail together**. Comparisons between architectures are therefore made at
equal component reliability.

### Proposition 3 (identical channels: the combined beta factor)

Let $G$ be a group of $m$ identical channels with physical beta factor $\beta_p$, holding the
same value of every attribute, with no other component holding those values. Then $G$ is
equivalent in distribution to a classical beta-factor group with total rate
$\Lambda = \lambda_p + \lambda_c$ and

```math
1 - \beta = (1 - \beta_p)(1 - \beta_c), \qquad \beta_c = \frac{\lambda_c}{\lambda_p + \lambda_c}.
```

*Proof.* The events that fail all of $G$ are the physical CCF event (rate $\beta_p\lambda_p$)
and the $|D|$ cyber events (rates $\lambda_d$). The superposition of independent Poisson
processes is Poisson with the summed rate, and all of these events have the same effect, so
for the structure function they are one event of rate $\beta_p\lambda_p + \lambda_c$. Each
member also keeps its own event of rate $(1-\beta_p)\lambda_p$. That is the beta-factor model
with $\Lambda = \lambda_p + \lambda_c$ and
$\beta = (\beta_p\lambda_p + \lambda_c)/\Lambda$. Then
$1 - \beta = (1-\beta_p)\lambda_p/\Lambda = (1-\beta_p)(1-\beta_c)$. $\square$

**Consequence.** Every beta-factor formula in use applies unchanged, with the effective
$\beta$ in place of $\beta_p$ and $\Lambda$ in place of $\lambda_p$. For a 1-of-$m$ group:

```math
Q_{1\text{-of-}m} = q_{cc} + (1 - q_{cc})\, q_i^{m}, \qquad q_{cc} = 1 - e^{-\beta\Lambda t}, \quad q_i = 1 - e^{-(1-\beta)\Lambda t}.
```

### Proposition 4 (full diversity)

If the members of $G$ hold pairwise distinct values of every attribute (and no component
outside $G$ holds them), $G$ is equivalent to a beta-factor group with total rate $\Lambda$ and

```math
\beta' = \frac{\beta_p \lambda_p}{\lambda_p + \lambda_c} = \beta_p (1 - \beta_c).
```

*Proof.* Each cyber event now fails one member, so it merges (superposition) with that
member's own physical event into one event of rate $(1-\beta_p)\lambda_p + \lambda_c$. The only
shared event is the physical one, of rate $\beta_p\lambda_p$. $\square$

Diversity therefore does not remove cyber exposure; it moves it from the shared term to the
independent one, where redundancy can defend against it.

### Proposition 5 (diversifying never hurts a redundant group)

Let $G$ be the set of children of a parallel (1-of-$m$) block of $\phi$, its members appearing
nowhere else in $\phi$, and suppose no event fails both a member of $G$ and a component outside
$G$. Let $e$ be an event with $S_e = A \cup B \subseteq G$, $A \cap B = \emptyset$,
and probability $k$. Replace $e$ by two independent events $e_A$, $e_B$ with $S = A$ and
$S = B$ and the same probability $k$. Then the block's failure probability falls by exactly

```math
\Delta = k(1 - k)\, P(\bar U \cap \bar V) \ \ge\ 0,
```

where $U$ ($V$) is the event that every member of $A$ ($B$) fails from its other events. The
system's failure probability does not increase.

*Proof.* The block fails iff every member fails. Before the split this is
$\{e\} \cup (U \cap V)$, with probability $k + (1-k)P(U \cap V)$, since $e$ is independent of
$U$ and $V$. After it, $(\{e_A\} \cup U) \cap (\{e_B\} \cup V)$, with probability
$k^2 + k(1-k)\left[P(U) + P(V)\right] + (1-k)^2 P(U \cap V)$. The difference is
$k(1-k)\left[1 - P(U) - P(V) + P(U \cap V)\right] = k(1-k)P(\bar U \cap \bar V)$. No event acts
both inside and outside the block, so the block's state is independent of the other
components' states, and a coherent system's failure probability is non-decreasing in the failure
probability of an independent module (Barlow & Proschan, 1975). $\square$

**Corollary.** Refining an attribute's values within a redundant group (giving some members
new, distinct values) is a sequence of such splits, so it never increases $Q$. In particular
full diversity is never worse than identical channels, and
$Q_{\text{diverse}} \le Q_{\text{identical}}$ in Propositions 3-4.

### Proposition 6 (common cause hurts redundant groups, and only those)

(a) If $G$ is as in Proposition 5, adding any physical CCF model or any shared cyber events on
$G$ (at fixed marginals) never decreases $Q$.
(b) This fails for groups in series: for two components in series with a shared event,
$Q$ can decrease.

*Proof.* (a) The members' failure indicators are non-decreasing functions of independent
$Y_e$, hence associated (Esary, Proschan & Walkup, 1967), so
$P(\cap_{j \in G} \{x_j = 0\}) \ge \prod_{j} P(x_j = 0)$, and the right side is the
independent value by Proposition 2. Monotonicity in the module finishes it as in Proposition 5 (with the same hypothesis that no
event acts both inside and outside $G$).
For the beta factor it is Jensen's inequality: with $a = 1 - q_{cc}$,
$1 - a + a q_i^{m} \ge (1 - a + a q_i)^m$. (b) Two components in series, rate $\lambda$ each,
$\lambda t = 0.1$: independent, $Q = 1 - e^{-0.2} = 0.181$; with half of each rate shared,
$Q = 1 - e^{-0.15} = 0.139$. $\square$

This makes the plan's validation check precise: "CCF-adjusted reliability is never above the
independence estimate" holds for common-cause groups that are redundant sets, which is the
only place CCF models are applied in this repository.

### Proposition 7 (the floor and the best possible gain)

For a 1-of-$m$ group of identical channels (Proposition 3), for every $m$,

```math
Q_{1\text{-of-}m} \ \ge\ 1 - e^{-\beta\Lambda t}, \qquad
\frac{Q_{1\text{-of-}1}}{Q_{1\text{-of-}m}} \ \le\ \frac{1 - e^{-\Lambda t}}{1 - e^{-\beta\Lambda t}} \ \approx\ \frac{1}{\beta} \quad (\Lambda t \ll 1).
```

*Proof.* The group fails whenever the common event occurs. $\square$

The best any amount of identical redundancy can buy is a factor $1/\beta$, with
$\beta = 1 - (1-\beta_p)(1-\beta_c)$. With $\beta_p = 0.02$ alone, that is 50; with the
illustrative cyber exposure of an EGI ($\beta_c = 0.078$), about 10. The cyber term enters the
bound exactly as the physical one does.

### Proposition 8 (factorisation of order-one events)

If every shared event $e$ is a cut set of order one (its occurrence alone fails the system),
then

```math
1 - Q = (1 - Q_0) \prod_{e \text{ shared}} (1 - q_e),
```

where $Q_0$ is the failure probability of the model with the shared events removed.

*Proof.* The system works iff no shared event occurs and the rest works; the shared events are
independent of the rest. $\square$

For identical architectures this applies to every CCF event of the navigation system, and
gives the hand-derived oracles of the tests.

## 3. What the model assumes

1. **Per-value rates.** A shared vulnerability's rate does not grow with the number of
   holders. This makes Proposition 2 hold and architectures comparable, but it is an
   assumption about attackers: if the attack rate grows with the attack surface, merging
   attribute values (one segment for many nodes) is penalised, not rewarded. Lesson 3 shows
   the navigation result moving with this choice.
2. **Independent Poisson events.** Attackers can choose timing; correlated or adaptive attacks
   (an attacker who waits for a mission-critical phase) are outside the model.
3. **All-or-nothing effect.** A shared-vulnerability event defeats every holder fully.
   Partial compromise and data corruption without loss are other failure modes.
4. **Parameter values.** $\nu_d$ and $p_d$ have no field-data basis. Every conclusion is shown
   over a range; the robust conclusions are the structural ones (Propositions 3-7), which hold
   for every value.

## References

* R. E. Barlow and F. Proschan, *Statistical Theory of Reliability and Life Testing*, 1975.
* R. E. Bryant, "Graph-based algorithms for Boolean function manipulation," *IEEE Trans.
  Computers* C-35(8), 1986.
* J. D. Esary, F. Proschan and D. W. Walkup, "Association of random variables, with
  applications," *Annals of Mathematical Statistics* 38(5), 1967.
* K. N. Fleming, GA-A13284, 1975 (the beta factor).
* A. Mosleh, D. M. Rasmuson and F. M. Marshall, NUREG/CR-5485, U.S. NRC, 1998.
* A. Rauzy, "New algorithms for fault trees analysis," *Reliability Engineering & System
  Safety* 40(3), 1993.
