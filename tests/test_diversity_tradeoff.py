"""Phase 4: architectures, costs and Pareto fronts."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from cyberccf.architecture_diversity_tradeoff import (
    Architecture,
    best_within_budget,
    cost,
    enumerate_architectures,
    load_costs,
    make_architecture,
    pareto_front,
    unreliability_at_scale,
)
from cyberccf.cyber_ccf_model import DIMENSIONS, cyber_ccf_model
from cyberccf.independence_baseline import MISSION_HOURS, unreliability
from cyberccf.physical_ccf_beta_factor import physical_ccf_model

point = st.tuples(st.integers(0, 20).map(float), st.integers(0, 20).map(float), st.integers())


@given(st.lists(point, max_size=25))
def test_pareto_front_matches_brute_force(points: list[tuple[float, float, int]]) -> None:
    front = pareto_front(points)

    def dominated(p: tuple[float, float, int]) -> bool:
        return any(q[0] <= p[0] and q[1] <= p[1] and (q[0] < p[0] or q[1] < p[1]) for q in points)

    expected = {(p[0], p[1]) for p in points if not dominated(p)}
    assert {(p[0], p[1]) for p in front} == expected
    assert len(front) == len(expected)  # duplicates of one front point are kept once
    assert all(a[1] > b[1] for a, b in zip(front, front[1:], strict=False))


def test_best_within_budget() -> None:
    pts = [(0.0, 5.0, "a"), (10.0, 2.0, "b"), (20.0, 1.0, "c"), (10.0, 2.0, "d")]
    assert best_within_budget(pts, 15.0) == (10.0, 2.0, "b")
    assert best_within_budget(pts, 100.0) == (20.0, 1.0, "c")
    assert best_within_budget(pts, -1.0) is None


def test_enumeration_covers_every_design() -> None:
    archs = list(enumerate_architectures())
    # (2 EGI: 2^3 + 3 EGI: 3^3) x (1 MC: 1 + 2 MC: 2^3)
    assert len(archs) == (8 + 27) * (1 + 8)
    assert len(set(archs)) == len(archs)
    assert make_architecture(2, 1) in archs


def test_costs_are_labelled_and_add_up() -> None:
    costs = load_costs()
    assert all("assumption" in c.basis and "no real cost data" in c.basis for c in costs.values())
    assert cost(make_architecture(2, 1)) == 0.0
    full = {("nav_source", d): 3 for d in DIMENSIONS} | {
        ("mission_computer", d): 2 for d in DIMENSIONS
    }
    expected = 10 + 15 + 2 * (20 + 2 + 8) + (30 + 2 + 8)
    assert cost(make_architecture(3, 2, full)) == expected


def test_labels() -> None:
    a = make_architecture(3, 2, {("nav_source", "firmware"): 2, ("mission_computer", "network"): 2})
    assert a.label == "3 EGI [fw 2] + 2 MC [net 2]"
    assert make_architecture(2, 1, {("nav_source", "firmware"): 1}) == Architecture(2, 1, ())


@pytest.mark.parametrize("scale", [0.0, 0.5, 1.0, 4.0])
def test_unreliability_at_scale_equals_rebuilding_the_model(scale: float) -> None:
    arch = make_architecture(3, 2, {("nav_source", "firmware"): 2})
    expected = unreliability(
        cyber_ccf_model(3, 2, 2, distinct=arch.distinct_map(), exposure_scale=scale), MISSION_HOURS
    )
    assert unreliability_at_scale(arch.model(), MISSION_HOURS, scale) == pytest.approx(
        expected, rel=1e-12
    )
    with pytest.raises(ValueError):
        unreliability_at_scale(arch.model(), MISSION_HOURS, -1.0)


def test_without_cyber_exposure_diversity_changes_nothing() -> None:
    # Sweep endpoint: at zero exposure every diversity level of a given unit count equals the
    # physical CCF model (Proposition 1).
    for n_egi, n_mc in [(2, 1), (3, 2)]:
        physical = unreliability(physical_ccf_model(n_egi, 2, n_mc), MISSION_HOURS)
        for arch in enumerate_architectures((n_egi,), (n_mc,)):
            got = unreliability_at_scale(arch.model(), MISSION_HOURS, 0.0)
            assert got == pytest.approx(physical, rel=1e-12)


def test_refining_any_attribute_never_increases_unreliability() -> None:
    # Corollary of Proposition 5 across the enumerated designs with two EGIs and two computers.
    archs = {
        a: unreliability(a.model(), MISSION_HOURS) for a in enumerate_architectures((2,), (2,))
    }
    for a, qa in archs.items():
        for b, qb in archs.items():
            da, db = a.distinct_map(), b.distinct_map()
            keys = set(da) | set(db)
            if all(db.get(k, 1) >= da.get(k, 1) for k in keys):  # b refines a
                assert qb <= qa * (1 + 1e-12)
