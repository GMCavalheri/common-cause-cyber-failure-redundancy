# `case_study_application`: redundancy as claimed vs as it is

**Lesson:** [5 · Redundancy as claimed vs as it is](lessons/05-redundancy-as-claimed-vs-as-it-is.md) ·
**Report:** [`report.md`](report.md) ·
**Code:** [`src/cyberccf/case_study_application/`](../src/cyberccf/case_study_application/)

## What it computes

* `views(arch)`: P(loss of navigation) under independence, physical CCF and physical + cyber
  CCF, the last also at both ends of the exposure range (0.25 to 10 times).
* `tornado(arch)`: one-at-a-time swings of every physical rate (0.5 to 2 times), beta factor
  (its IEC range) and cyber exposure (0 to 10 times).
* `recommend()`: the cheapest design meeting an illustrative requirement ($10^{-4}$ per
  10-hour mission) at the top of the exposure range, which is the worst case because
  unreliability never decreases with exposure.
* `unreliability_with(model, hours, factor)`: rescale any subset of event rates on one BDD.

## Verification

The redundant design's three numbers against closed forms derived by hand; the ordering of the
views on several designs; the tornado's consistency; the recommendation on a small candidate
set.
