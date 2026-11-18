# Lesson 8 · What is (and isn't) new

> A model is only as useful as the honesty of the claims made with it. This last lesson reads
> the project against the work it stands on, separates what is borrowed from what is added,
> and practises the skill a research paper will demand: stating a contribution as narrowly as
> the evidence allows, and saying what must still be checked before stating it at all.

**Note:** [`docs/related-work.md`](../related-work.md) ·
**Derivation:** [`docs/derivation.md`](../derivation.md) ·
**Previous:** [Lesson 7](07-from-a-security-posture-to-a-number.md)

## Learning objectives

By the end of this lesson you should be able to:

1. Place this project's model among classical CCF methods, design-diversity theory,
   software-CCF work in nuclear instrumentation and control, and diversity-for-security
   research.
2. Distinguish an elementary result, a modelling choice, a worked example and a genuine
   contribution, and label each claim accordingly.
3. Write a novelty statement that would survive a hostile reviewer, and the search plan that
   must come before it.

---

## 1. Four neighbouring literatures

| literature | what it established | what it does not do |
|---|---|---|
| **Classical CCF** (Fleming 1975; NUREG/CR-5485, 1998) | common cause as root cause plus coupling factor; beta, MGL and alpha-factor models; basic-event formulation | consider a root cause that *seeks* the coupling factor |
| **Design diversity** (Avižienis 1985; Eckhardt & Lee 1985; Knight & Leveson 1986; Littlewood & Miller 1989) | independently developed versions still fail together; diversity helps but is not independence | treat attacks |
| **Software CCF in digital I&C** (Shorthill et al. 2022, INL) | software-centric coupling attributes; components in several overlapping common-cause groups; a modified beta factor | treat attacks; the paper never mentions security |
| **Diversity for security** (Geer et al. 2003; Littlewood & Strigini 2004; Cox et al. 2006; Zhang et al. 2016) | monoculture as a common mode; probabilistic reasoning about diversity and independence for security; diversity as a mechanism and as a metric of attacker effort | express the effect in reliability quantities (beta, unreliability, MTBF) next to physical common cause |

The project sits where these meet. That location is its contribution; very little of its
mathematics is new.

## 2. Four kinds of claim

A hostile reviewer will sort every claim into one of four bins. It is better to do it first.

1. **Elementary results.** True by a few lines of probability, and any reviewer can derive
   them: the combined beta $1 - \beta = (1 - \beta_p)(1 - \beta_c)$ (superposition of Poisson
   processes), the floor and the $1/\beta$ bound, the split-gain identity
   $k(1-k)P(\bar U \cap \bar V)$. Their value is not depth; it is that they let an existing
   calculation absorb the correction, and that they make the plan's directionality check
   precise (common cause hurts redundant groups, and can help series ones).
2. **Modelling choices.** Defensible but not forced: the per-value rate (a component's exposure
   does not depend on who else shares its attributes), independent events for distinct values
   (the optimistic end of the Eckhardt-Lee picture), all-or-nothing effects, independent
   repair after a common-cause event. Each is stated where it is used, and Lesson 3 shows one
   result (the shared network segment) moving with one of them.
3. **Worked examples.** The navigation case study: synthetic, illustrative rates, every number
   conditional. Its value is the *structure* of the result (2.74 → 1.60 → 0.88 orders of
   magnitude; diversity restoring the physical figure and removing the sensitivity), which
   survives any reasonable change of the numbers.
4. **Contributions.** What remains when the other three are subtracted: a model that puts
   shared, attacker-exercised vulnerabilities into the beta-factor calculation a reliability
   engineer already does, combined in closed form with physical common cause; the structural
   results about diversity, cost and exposure; and the mapping from a NIST posture to a
   *range* of exposure, with the observation that posture moves the range but cannot remove the
   sharing (SC-29 is in no baseline).

The [related-work note](../related-work.md) applies this sorting claim by claim.

## 3. The closest neighbour, read carefully

Shorthill, Bao, Chen and Ban (2022) is the paper a reviewer would cite against this project.
Their coupling attributes and overlapping groups are structurally what Lesson 3 calls attribute
events. The differences are real but must be stated precisely:

* their root cause is a **software design fault**; here it is an **attacker exercising a shared
  vulnerability**, which changes how the rate is built (attempts times success probability)
  and what lowers it (security controls, Lesson 7);
* their parameters come from software-specific estimation where operational data are missing;
  here, parameters are explicitly illustrative and every conclusion is shown over a range;
* this project adds the conservation of marginals, the closed-form combination with physical
  beta, the exact diversity identity, and the cost and posture analyses.

A paper that did not cite them, or that claimed "the first model of overlapping common-cause
groups", would deserve rejection.

## 4. The novelty statement

> We extend the beta-factor common-cause model to shared vulnerabilities exercised by an
> attacker, defining a cyber beta factor from attribute-defined events whose rates conserve
> each component's exposure. For identical channels the physical and cyber factors combine as
> $1 - \beta = (1 - \beta_p)(1 - \beta_c)$, so existing calculations absorb the correction; we
> prove that diversifying an attribute never increases the failure probability of a redundant
> group and give the exact gain. On a synthetic avionics-style navigation system, the benefit
> claimed for redundancy falls from 2.7 to 0.9 orders of magnitude, while a diverse design keeps
> the physical-CCF figure and becomes insensitive to the unknown cyber exposure.

Every clause is supported by a proposition, a test or a result table; none says "first".
Before the paper uses even this, section 6 of the related-work note lists the systematic search
still to be done: *Reliability Engineering & System Safety*, *IEEE Transactions on Reliability*,
PSAM and RAMS proceedings, NRC, EPRI and NEI digital I&C guidance, and forward citations of the
two closest papers.

## 5. What would make it stronger

* **Data.** Even coarse incident counts of shared-vulnerability events across redundant
  industrial or avionics channels would turn the illustrative exposure into an estimate, as
  NUREG/CR-6268 did for physical CCF.
* **Coincident vulnerabilities.** Replace "distinct values are independent" by an
  Eckhardt-Lee-style model in which different implementations share some difficulty for the
  attacker.
* **Adaptive attackers.** Timing chosen for the worst mission phase breaks the Poisson
  assumption; a game-theoretic or phase-aware model would test how much.
* **A real architecture.** The method needs only a block diagram, failure rates and attributes;
  applying it to a public reference architecture would test its usability.

## Exercises

1. Pick one row of the novelty table in the related-work note and argue the opposite
   assessment, as a reviewer would. Then answer the review.
2. Rewrite the novelty statement of section 4 for a practitioner audience in three sentences,
   without any formula.
3. Which single modelling choice of section 2, if wrong, would most change the case study's
   conclusion? Justify with a result from Lessons 3-5.
4. Design the search query you would run in *Reliability Engineering & System Safety* first,
   and say what result would force you to change the novelty statement.

### Solutions

1. Example, the split-gain identity: "this is a two-line consequence of inclusion-exclusion and
   adds nothing." Answer: agreed that it is elementary; the contribution is its use, an exact and
   universal statement that diversity never hurts redundant groups, and the counterexample that
   bounds the plan's directionality check. The paper should present it as a lemma, not a theorem.
2. "Redundant channels that run the same software, sit on the same network or come from the
   same supplier can be defeated by one attack, which standard reliability calculations ignore.
   We show how to add that risk to the calculation engineers already use, and that on a typical
   design it erases most of the benefit claimed for redundancy. Making the channels diverse
   restores the benefit and makes the result insensitive to how likely attacks are, which nobody
   can currently estimate."
3. Independence of distinct values (Proposition 4). The case study's recommendation rests on
   diversity removing the cyber term from the order-one cut sets; if diverse implementations
   shared vulnerabilities with some probability, the diverse design's floor would rise with the
   exposure, and the "insensitive to the exposure" result of Lessons 4-5 would weaken in
   proportion.
4. For example: ("common cause" OR "common-cause" OR "common mode") AND (cyber OR security OR
   attack OR vulnerability) AND (redundan* OR diversity) AND ("beta factor" OR "reliability").
   A paper that combined a shared-vulnerability term with the physical beta factor in closed form
   would force the statement to drop that clause and cite it.

## References

See [`docs/related-work.md`](../related-work.md) for the full, checked list.
