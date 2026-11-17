"""Numerical checks of every proposition in docs/derivation.md."""

from __future__ import annotations

import math

import numpy as np

from cyberccf.cyber_ccf_model import (
    DIMENSIONS,
    Exposure,
    apply_cyber,
    combined_beta,
    cyber_ccf_model,
    split_gain,
    total_rate,
)
from cyberccf.independence_baseline import (
    MISSION_HOURS,
    Parallel,
    Series,
    failure_probability,
    independent_model,
    navigation_model,
    system_works,
    unreliability,
)
from cyberccf.physical_ccf_beta_factor import apply_ccf, beta_group, physical_ccf_model

from common import table, write_result

LP = 2e-4
ALL_DIVERSE = {(g, d): 2 for g in ("nav_source", "mission_computer") for d in DIMENSIONS}
NO_BETA = dict.fromkeys(("nav_source", "data_bus", "power", "mission_computer"), 0.0)


def group(m: int, beta_p: float, lc: float, values: list[str], lp: float = LP):
    names = [f"c{i}" for i in range(m)]
    model = independent_model("g", Parallel(*names), dict.fromkeys(names, lp))
    if beta_p > 0:
        model = apply_ccf(model, beta_group("p", names, beta_p))
    exp = {"firmware": Exposure("firmware", lc, 1.0)}
    return apply_cyber(model, {n: {"firmware": v} for n, v in zip(names, values, strict=True)}, exp)


def beta_equivalent_group(m: int, rate: float, beta: float):
    names = [f"c{i}" for i in range(m)]
    model = independent_model("b", Parallel(*names), dict.fromkeys(names, rate))
    return apply_ccf(model, beta_group("b", names, beta)) if beta > 0 else model


def bound(x: float) -> str:
    """Rounding-level errors differ across CPUs, so they are reported as a bound."""
    if x > 1e-12:
        raise AssertionError(f"check failed: error {x}")
    return "< 1e-12"


def rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-300)


def main() -> None:
    rows = []
    t = MISSION_HOURS

    # P1: reductions.
    e1 = abs(
        unreliability(cyber_ccf_model(mission_computers=2, exposure_scale=0.0), t)
        - unreliability(physical_ccf_model(mission_computers=2), t)
    )
    e2 = abs(
        unreliability(physical_ccf_model(mission_computers=2, betas=NO_BETA), t)
        - unreliability(navigation_model(mission_computers=2), t)
    )
    rows.append(
        ["1", "zero cyber rates = physical model; zero beta = independence", 2, max(e1, e2), "abs"]
    )

    # P2: marginals are conserved in every architecture.
    worst = 0.0
    cases = 0
    for distinct in ({}, {("nav_source", "firmware"): 2}, ALL_DIVERSE):
        for shared in (False, True):
            model = cyber_ccf_model(mission_computers=2, distinct=distinct, shared_network=shared)
            q = model.probabilities(t)
            for comp in model.components:
                lam = sum(model.event(e).rate_per_hour for e in model.causes[comp])
                survive = math.prod(1 - q[e] for e in model.causes[comp])
                worst = max(worst, rel(1 - survive, -math.expm1(-lam * t)))
                cases += 1
            ref = cyber_ccf_model(mission_computers=2)
            assert all(
                math.isclose(total_rate(model, c), total_rate(ref, c), rel_tol=1e-12)
                for c in model.components
            )
    rows.append(
        ["2", "each component fails with 1 − exp(−Λt), any architecture", cases, worst, "rel"]
    )

    # P3 and P4: identical and fully diverse groups equal beta-factor groups.
    worst3 = worst4 = 0.0
    n = 0
    for m in (2, 3, 4):
        for beta_p in (0.0, 0.02, 0.1):
            for lc in (1e-6, 1.7e-5, 1e-4):
                lam = LP + lc
                beta_c = lc / lam
                same = unreliability(group(m, beta_p, lc, ["A"] * m), t)
                ref = unreliability(beta_equivalent_group(m, lam, combined_beta(beta_p, beta_c)), t)
                worst3 = max(worst3, rel(same, ref))
                diverse = unreliability(group(m, beta_p, lc, [f"V{i}" for i in range(m)]), t)
                ref4 = unreliability(beta_equivalent_group(m, lam, beta_p * (1 - beta_c)), t)
                worst4 = max(worst4, rel(diverse, ref4))
                n += 1
    rows.append(
        ["3", "identical channels = beta group with 1 − β = (1 − β_p)(1 − β_c)", n, worst3, "rel"]
    )
    rows.append(
        ["4", "fully diverse channels = beta group with β' = β_p(1 − β_c)", n, worst4, "rel"]
    )

    # P5: split gain identity on random probabilities, and refinement chains on navigation.
    rng = np.random.default_rng(20261117)
    worst5 = 0.0
    names = ["x", "y"]
    base = apply_ccf(
        independent_model("g", Parallel(*names), {"x": 1.0, "y": 1.0}), beta_group("o", names, 0.5)
    )
    exp = {"firmware": Exposure("firmware", 1.0, 1.0)}
    shared = apply_cyber(base, {"x": {"firmware": "K"}, "y": {"firmware": "K"}}, exp)
    split = apply_cyber(base, {"x": {"firmware": "K1"}, "y": {"firmware": "K2"}}, exp)
    for _ in range(1000):
        k, a, b, c = rng.random(4)
        qs = {"x": a, "y": b, "o[x+y]": c, "cyber:firmware=K": k}
        qp = {"x": a, "y": b, "o[x+y]": c, "cyber:firmware=K1": k, "cyber:firmware=K2": k}
        drop = failure_probability(shared, qs) - failure_probability(split, qp)
        pu, pv = 1 - (1 - a) * (1 - c), 1 - (1 - b) * (1 - c)
        worst5 = max(worst5, abs(drop - split_gain(k, pu, pv, c + (1 - c) * a * b)))
    rows.append(
        ["5", "split gain = k(1 − k)P(not U, not V), random probabilities", 1000, worst5, "abs"]
    )
    chain = [
        {},
        {("nav_source", "firmware"): 2},
        {("nav_source", "firmware"): 2, ("mission_computer", "firmware"): 2},
        ALL_DIVERSE,
    ]
    qs_chain = [unreliability(cyber_ccf_model(mission_computers=2, distinct=d), t) for d in chain]
    monotone = all(b <= a * (1 + 1e-12) for a, b in zip(qs_chain, qs_chain[1:], strict=False))
    rows.append(
        [
            "5",
            "navigation refinement chain never increases Q",
            len(chain),
            "holds" if monotone else "FAILS",
            "—",
        ]
    )

    # P6: ordering on the navigation system, and the series counterexample.
    q_ind = unreliability(navigation_model(mission_computers=2), t)
    q_phys = unreliability(physical_ccf_model(mission_computers=2), t)
    q_cyb = unreliability(cyber_ccf_model(mission_computers=2), t)
    rows.append(
        [
            "6a",
            "independence ≤ physical CCF ≤ physical + cyber (navigation)",
            1,
            "holds" if q_ind <= q_phys <= q_cyb else "FAILS",
            "—",
        ]
    )
    s = independent_model("s", Series("a", "b"), {"a": 0.01, "b": 0.01})
    s_ccf = apply_ccf(s, beta_group("g", ["a", "b"], 0.5))
    e6 = max(
        abs(unreliability(s, t) - (1 - math.exp(-0.2))),
        abs(unreliability(s_ccf, t) - (1 - math.exp(-0.15))),
    )
    rows.append(["6b", "series counterexample: 0.181 → 0.139", 1, e6, "abs"])

    # P7: the floor and the gain bound.
    floor_ok = True
    for beta_p in (0.02, 0.05):
        for lc in (0.0, 1.7e-5):
            lam = LP + lc
            beta = combined_beta(beta_p, lc / lam)
            floor = -math.expm1(-beta * lam * t)
            q1 = unreliability(group(1, 0.0, lc, ["A"]), t) if lc else -math.expm1(-LP * t)
            for m in range(2, 7):
                qm = unreliability(group(m, beta_p, lc, ["A"] * m), t)
                floor_ok &= qm >= floor * (1 - 1e-12)
                floor_ok &= q1 / qm <= (-math.expm1(-lam * t)) / floor * (1 + 1e-12)
    rows.append(
        [
            "7",
            "Q ≥ 1 − e^(−βΛt) and gain ≤ (1 − e^(−Λt))/(1 − e^(−βΛt))",
            20,
            "holds" if floor_ok else "FAILS",
            "—",
        ]
    )

    # P8: factorisation of order-one events (identical navigation).
    worst8 = 0.0
    for mcs in (1, 2):
        model = cyber_ccf_model(mission_computers=mcs)
        q = model.probabilities(t)
        names = [e.name for e in model.events]
        order_one = [e for e in names if not system_works(model, {n: n == e for n in names})]
        q0 = failure_probability(model, {n: 0.0 if n in order_one else q[n] for n in names})
        r_fact = (1 - q0) * math.prod(1 - q[e] for e in order_one)
        worst8 = max(worst8, rel(1 - r_fact, unreliability(model, t)))
    rows.append(["8", "1 − Q = (1 − Q₀) ∏(1 − q_e) over order-one events", 2, worst8, "rel"])

    rows = [[*r[:3], bound(r[3]) if isinstance(r[3], float) else r[3], r[4]] for r in rows]
    summary = table(["proposition", "check", "cases", "worst error", "error kind"], rows)
    write_result(
        "reduction_checks",
        "Numerical checks of the propositions in docs/derivation.md",
        [("Checks", summary)],
    )


if __name__ == "__main__":
    main()
