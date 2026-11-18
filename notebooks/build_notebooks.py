"""Generate and execute the demo notebooks, one per lesson, from the cell sources below.

    uv run python notebooks/build_notebooks.py           # write and execute all notebooks
    uv run python notebooks/build_notebooks.py --check   # execute in memory only (CI)

Keeping the sources here, instead of hand-editing .ipynb JSON, makes the notebooks reviewable
in diffs. Every computation in them is exact or seeded and runs in seconds; the headline numbers
live in ``validation/results/``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

HERE = Path(__file__).resolve().parent

SETUP = """\
import matplotlib.pyplot as plt
import numpy as np

from cyberccf import plotting
from cyberccf.independence_baseline import MISSION_HOURS, navigation_model, unreliability

plotting.use_style()"""

Cell = tuple[str, str]

NOTEBOOKS: dict[str, list[Cell]] = {
    "01_the_independence_assumption.ipynb": [
        (
            "md",
            """\
# 1 · The independence assumption

The navigation system under the classical independence assumption, its minimal cut sets, and
what redundancy is claimed to buy. See [Lesson 1](../docs/lessons/01-the-independence-assumption.md).""",
        ),
        ("code", SETUP),
        (
            "code",
            """\
from cyberccf.independence_baseline import describe, minimal_cut_sets

single = navigation_model()
dual = navigation_model(mission_computers=2)
print(describe(single.structure))
print(f"P(loss), one computer:  {unreliability(single, MISSION_HOURS):.4e}")
print(f"P(loss), two computers: {unreliability(dual, MISSION_HOURS):.4e}")
q = single.probabilities(MISSION_HOURS)
for cut in sorted(minimal_cut_sets(single), key=lambda c: -np.prod([q[e] for e in c])):
    print(f"{' + '.join(sorted(cut)):32s} {np.prod([q[e] for e in cut]):.3e}")""",
        ),
        (
            "code",
            """\
q_egi = q["egi_1"]
ns = np.arange(1, 7)
fig, ax = plt.subplots(figsize=(5, 3))
ax.semilogy(ns, q_egi**ns, "o-", color=plotting.INDEPENDENT_COLOR)
ax.set_xlabel("identical channels (1-of-n)")
ax.set_ylabel("P(all fail in 10 h)")
ax.set_title("What independence promises: q^n");""",
        ),
    ],
    "02_when_one_cause_breaks_two_channels.ipynb": [
        (
            "md",
            """\
# 2 · When one cause breaks two channels

The beta factor's floor, MGL and alpha-factor fractions, and physical common cause on the
navigation system. See [Lesson 2](../docs/lessons/02-when-one-cause-breaks-two-channels.md).""",
        ),
        ("code", SETUP),
        (
            "code",
            """\
from cyberccf.physical_ccf_beta_factor import ccf_floor, one_of_m_beta_unreliability

for beta in (0.0, 0.02, 0.1):
    row = [one_of_m_beta_unreliability(m, 2e-4, beta, MISSION_HOURS) for m in range(1, 5)]
    print(f"beta {beta:4}: " + "  ".join(f"{x:.2e}" for x in row), f" floor {ccf_floor(2e-4, beta, MISSION_HOURS):.2e}")""",
        ),
        (
            "code",
            """\
from cyberccf.physical_ccf_beta_factor import alpha_fractions, mgl_fractions

print("MGL m=3, beta 0.1, gamma 0.3:", np.round(mgl_fractions(3, [0.1, 0.3]), 4))
print("alpha staggered:    ", np.round(alpha_fractions(3, [0.95, 0.03, 0.02], True), 4))
print("alpha non-staggered:", np.round(alpha_fractions(3, [0.95, 0.03, 0.02], False), 4))""",
        ),
        (
            "code",
            """\
from cyberccf.physical_ccf_beta_factor import physical_ccf_model

for mc in (1, 2):
    ind = unreliability(navigation_model(mission_computers=mc), MISSION_HOURS)
    ccf = unreliability(physical_ccf_model(mission_computers=mc), MISSION_HOURS)
    print(f"{mc} computer(s): independence {ind:.3e}, physical CCF {ccf:.3e}, ratio {ccf / ind:.1f}")""",
        ),
    ],
    "03_the_cyber_beta_factor.ipynb": [
        (
            "md",
            """\
# 3 · The cyber beta factor

Shared vulnerabilities as common-cause events, the combined beta factor, and the exact gain of
diversifying. See [Lesson 3](../docs/lessons/03-the-cyber-beta-factor.md).""",
        ),
        ("code", SETUP),
        (
            "code",
            """\
from cyberccf.cyber_ccf_model import combined_beta, common_cause_share, cyber_beta, cyber_ccf_model

model = cyber_ccf_model(mission_computers=2)
b_c = cyber_beta(model, "egi_1")
print(f"cyber beta of an EGI: {b_c:.4f}")
print(f"effective beta: {common_cause_share(model, 'egi_1'):.4f} = 1 - (1 - 0.02)(1 - {b_c:.4f}) = {combined_beta(0.02, b_c):.4f}")
print(f"P(loss): {unreliability(model, MISSION_HOURS):.4e}")""",
        ),
        (
            "code",
            """\
from cyberccf.cyber_ccf_model import diverse_group_unreliability, identical_group_unreliability

scales = np.linspace(0, 10, 21)
lc = 1.7e-5
ident = [identical_group_unreliability(2, 2e-4, 0.02, s * lc, MISSION_HOURS) for s in scales]
div = [diverse_group_unreliability(2, 2e-4, 0.02, s * lc, MISSION_HOURS) for s in scales]
fig, ax = plt.subplots(figsize=(5, 3))
ax.semilogy(scales, ident, color=plotting.CYBER_COLOR, label="identical pair")
ax.semilogy(scales, div, "--", color="#3a8f5c", label="diverse pair")
ax.set_xlabel("cyber exposure (x illustrative)")
ax.set_ylabel("P(pair fails in 10 h)")
ax.legend();""",
        ),
        (
            "code",
            """\
from cyberccf.cyber_ccf_model import split_gain

# Splitting a shared event of probability k: the drop is k(1-k)P(not U and not V) >= 0.
rng = np.random.default_rng(0)
k, pu, pv = rng.random(3)
print("drop with independent U, V:", split_gain(k, pu, pv, pu * pv))""",
        ),
    ],
    "04_buying_independence.ipynb": [
        (
            "md",
            """\
# 4 · Buying independence

Designs with two EGIs and two mission computers, costed and quantified across the exposure
range. See [Lesson 4](../docs/lessons/04-buying-independence.md).""",
        ),
        ("code", SETUP),
        (
            "code",
            """\
from cyberccf.architecture_diversity_tradeoff import (
    cost,
    enumerate_architectures,
    pareto_front,
    unreliability_at_scale,
)

archs = list(enumerate_architectures((2,), (2,)))
models = {a: a.model() for a in archs}
fig, ax = plt.subplots(figsize=(6, 3.5))
for s, color in zip((0.0, 1.0, 10.0), plotting.SERIES_COLORS):
    pts = [(cost(a), unreliability_at_scale(models[a], MISSION_HOURS, s), a) for a in archs]
    front = pareto_front(pts)
    ax.step([p[0] for p in front], [p[1] for p in front], where="post", color=color, label=f"exposure x {s:g}")
ax.set_yscale("log")
ax.set_xlabel("relative cost (illustrative)")
ax.set_ylabel("P(loss in 10 h)")
ax.legend();
print(len(archs), "designs")""",
        ),
    ],
    "05_redundancy_as_claimed_vs_as_it_is.ipynb": [
        (
            "md",
            """\
# 5 · Redundancy as claimed vs as it is

The before-and-after of the case study, the tornado and the robust recommendation. See
[Lesson 5](../docs/lessons/05-redundancy-as-claimed-vs-as-it-is.md).""",
        ),
        ("code", SETUP),
        (
            "code",
            """\
from cyberccf.case_study_application import REDUNDANT, SINGLE_STRING, tornado, views

single, redundant = views(SINGLE_STRING, bus_channels=1), views(REDUNDANT)
for name in ("as_claimed", "physical", "cyber", "cyber_high"):
    ratio = getattr(single, name) / getattr(redundant, name)
    print(f"{name:11s} redundancy buys {ratio:7.1f}x ({np.log10(ratio):.2f} orders)")""",
        ),
        (
            "code",
            """\
for bar in tornado()[:5]:
    print(f"{bar.parameter:32s} {bar.q_low:.2e} .. {bar.q_high:.2e}")""",
        ),
        (
            "code",
            """\
from cyberccf.case_study_application import recommend

rec = recommend()
print(rec.architecture.label, "cost", rec.cost, f"P(loss) {rec.q_illustrative:.2e} .. {rec.q_worst:.2e}")""",
        ),
    ],
    "06_time_repair_and_a_simulation_that_checks_the_algebra.ipynb": [
        (
            "md",
            """\
# 6 · Time, repair and a simulation that checks the algebra

Availability and MTBF with repair, and the Monte Carlo checks. See
[Lesson 6](../docs/lessons/06-time-repair-and-a-simulation-that-checks-the-algebra.md).""",
        ),
        ("code", SETUP),
        (
            "code",
            """\
from cyberccf.cyber_ccf_model import cyber_ccf_model
from cyberccf.independence_baseline import component_specs
from cyberccf.physical_ccf_beta_factor import physical_ccf_model
from cyberccf.time_dependent import steady_state

mttr = {n: s.mttr_hours for n, s in component_specs(mission_computers=2).items()}
for label, model in [
    ("as claimed", navigation_model(mission_computers=2)),
    ("physical CCF", physical_ccf_model(mission_computers=2)),
    ("physical + cyber CCF", cyber_ccf_model(mission_computers=2)),
]:
    ss = steady_state(model, mttr)
    print(f"{label:22s} A {ss.availability:.7f}  MTBF {ss.mtbf:10.0f} h  MDT {ss.mdt:.2f} h")""",
        ),
        (
            "code",
            """\
from cyberccf.time_dependent import simulate_missions, transient_unreliability

model = cyber_ccf_model(mission_computers=2)
est = simulate_missions(model, 2000.0, 200_000, np.random.default_rng(1))
print(f"BDD {unreliability(model, 2000.0):.4f}  Markov {transient_unreliability(model, 2000.0):.4f}  "
      f"Monte Carlo {est.value:.4f} [{est.low:.4f}, {est.high:.4f}]")""",
        ),
    ],
    "07_from_a_security_posture_to_a_number.ipynb": [
        (
            "md",
            """\
# 7 · From a security posture to a number

A NIST SP 800-82r3 OT-overlay level as a range of exposure. See
[Lesson 7](../docs/lessons/07-from-a-security-posture-to-a-number.md).""",
        ),
        ("code", SETUP),
        (
            "code",
            """\
from cyberccf.case_study_application import REDUNDANT
from cyberccf.security_posture import LEVELS, controls_at, cyber_beta_range, unreliability_range

for level in LEVELS:
    n = {d: len(controls_at(level, d)) for d in ("firmware", "network", "supply_chain")}
    lo, hi = cyber_beta_range(level, 2e-4)
    q_lo, q_hi = unreliability_range(REDUNDANT, level)
    print(f"{level:9s} controls {n}  beta_c {lo:.3f}..{hi:.3f}  P(loss) {q_lo:.1e}..{q_hi:.1e}")""",
        ),
    ],
    "08_what_is_and_isnt_new.ipynb": [
        (
            "md",
            """\
# 8 · What is (and isn't) new

The propositions of the derivation, checked numerically. See
[Lesson 8](../docs/lessons/08-what-is-and-isnt-new.md) and
[docs/derivation.md](../docs/derivation.md).""",
        ),
        ("code", SETUP),
        (
            "code",
            """\
from cyberccf.cyber_ccf_model import Exposure, apply_cyber, combined_beta
from cyberccf.independence_baseline import Parallel, independent_model
from cyberccf.physical_ccf_beta_factor import apply_ccf, beta_group


def pair(beta_p, lc, values, rate=2e-4):
    m = independent_model("g", Parallel("a", "b"), {"a": rate, "b": rate})
    m = apply_ccf(m, beta_group("p", ["a", "b"], beta_p))
    return apply_cyber(m, {"a": {"firmware": values[0]}, "b": {"firmware": values[1]}},
                       {"firmware": Exposure("firmware", lc, 1.0)})


# Proposition 3: an identical pair is a beta-factor pair with the combined beta.
lc = 1.7e-5
lam = 2e-4 + lc
beta = combined_beta(0.02, lc / lam)
ref = apply_ccf(independent_model("r", Parallel("a", "b"), {"a": lam, "b": lam}), beta_group("r", ["a", "b"], beta))
print("Proposition 3:", unreliability(pair(0.02, lc, "AA"), 10.0), unreliability(ref, 10.0))
# Proposition 5: diversity never hurts a redundant group.
print("Proposition 5:", unreliability(pair(0.02, lc, "AB"), 10.0) <= unreliability(pair(0.02, lc, "AA"), 10.0))""",
        ),
    ],
}


def build(name: str, cells: list[Cell]) -> nbformat.NotebookNode:
    nb = nbformat.v4.new_notebook()
    nb.metadata["kernelspec"] = {
        "name": "python3",
        "display_name": "Python 3",
        "language": "python",
    }
    nb.cells = [
        nbformat.v4.new_markdown_cell(src) if kind == "md" else nbformat.v4.new_code_cell(src)
        for kind, src in cells
    ]
    for i, cell in enumerate(nb.cells):
        cell["id"] = f"{Path(name).stem}-{i}"
    NotebookClient(
        nb,
        timeout=900,
        kernel_name="python3",
        record_timing=False,  # no timestamps: rebuilds are byte-identical
        resources={"metadata": {"path": str(HERE)}},
    ).execute()
    return nb


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="execute without writing")
    ap.add_argument("names", nargs="*", help="notebooks to build (default: all)")
    args = ap.parse_args()
    for name in args.names or list(NOTEBOOKS):
        print(f"== {name}", flush=True)
        nb = build(name, NOTEBOOKS[name])
        if not args.check:
            nbformat.write(nb, HERE / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
