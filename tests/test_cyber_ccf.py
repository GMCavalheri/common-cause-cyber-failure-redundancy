"""Phase 3: shared cyber vulnerabilities as common cause, against closed forms and properties."""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cyberccf.cyber_ccf_model import (
    DIMENSIONS,
    Exposure,
    apply_cyber,
    combined_beta,
    common_cause_share,
    cyber_beta,
    cyber_beta_from_rates,
    cyber_ccf_model,
    cyber_event_name,
    cyber_rate_from_beta,
    diverse_group_unreliability,
    identical_group_unreliability,
    load_attribute_table,
    load_exposures,
    navigation_attributes,
    scaled,
    split_gain,
    total_rate,
)
from cyberccf.independence_baseline import (
    MISSION_HOURS,
    Parallel,
    Series,
    failure_probability,
    independent_model,
    unreliability,
)
from cyberccf.physical_ccf_beta_factor import apply_ccf, beta_group, physical_ccf_model

LP = 2e-4  # an EGI's physical rate (CPS-01/02 assumption)


def one_exposure(rate: float) -> dict[str, Exposure]:
    return {"firmware": Exposure("firmware", rate, 1.0)}


def group(
    m: int, beta_p: float, cyber_rate: float, values: list[str], k: int | None = None
) -> tuple[float, float]:
    """1-of-m group; member i holds firmware value values[i]. Returns (Q, cyber beta of c0)."""
    names = [f"c{i}" for i in range(m)]
    model = independent_model("g", Parallel(*names), dict.fromkeys(names, LP))
    if beta_p > 0:
        model = apply_ccf(model, beta_group("p", names, beta_p))
    model = apply_cyber(
        model,
        {n: {"firmware": v} for n, v in zip(names, values, strict=True)},
        one_exposure(cyber_rate),
    )
    return unreliability(model, MISSION_HOURS), cyber_beta(model, "c0")


# --- data -------------------------------------------------------------------------------------


def test_exposures_are_labelled_assumptions() -> None:
    exp = load_exposures()
    assert set(exp) == set(DIMENSIONS)
    for e in exp.values():
        assert "assumption" in e.basis and "no field data" in e.basis
        assert e.rate_per_hour == e.attempt_rate_per_hour * e.success_probability


def test_attribute_table_covers_the_programmable_groups() -> None:
    table = load_attribute_table()
    assert set(table) == {"nav_source", "mission_computer"}


def test_exposure_validation_and_scaling() -> None:
    with pytest.raises(ValueError):
        Exposure("bios", 1.0, 0.5)
    with pytest.raises(ValueError):
        Exposure("firmware", -1.0, 0.5)
    with pytest.raises(ValueError):
        Exposure("firmware", 1.0, 1.5)
    with pytest.raises(ValueError):
        scaled(load_exposures(), -1.0)
    doubled = scaled(load_exposures(), 2.0)
    assert doubled["network"].rate_per_hour == pytest.approx(
        2 * load_exposures()["network"].rate_per_hour
    )


# --- closed forms -------------------------------------------------------------------------------


@pytest.mark.parametrize("m", [2, 3, 4])
@pytest.mark.parametrize("beta_p", [0.0, 0.02])
@pytest.mark.parametrize("lc", [0.0, 1e-5, 1e-4])
def test_identical_and_diverse_groups_match_closed_forms(m: int, beta_p: float, lc: float) -> None:
    same, _ = group(m, beta_p, lc, ["A"] * m)
    diverse, _ = group(m, beta_p, lc, [f"V{i}" for i in range(m)])
    assert same == pytest.approx(
        identical_group_unreliability(m, LP, beta_p, lc, MISSION_HOURS), rel=1e-12
    )
    assert diverse == pytest.approx(
        diverse_group_unreliability(m, LP, beta_p, lc, MISSION_HOURS), rel=1e-12
    )
    assert diverse <= same * (1 + 1e-12)


@given(st.floats(0.0, 0.5), st.floats(0.0, 0.99))
def test_cyber_beta_definitions_agree(beta_p: float, beta_c: float) -> None:
    lc = cyber_rate_from_beta(LP, beta_c)
    assert cyber_beta_from_rates(LP, lc) == pytest.approx(beta_c, abs=1e-12)
    names = ["a", "b"]
    model = independent_model("g", Parallel(*names), dict.fromkeys(names, LP))
    if beta_p > 0:
        model = apply_ccf(model, beta_group("p", names, beta_p))
    model = apply_cyber(model, {n: {"firmware": "A"} for n in names}, one_exposure(lc))
    if lc > 0:
        assert cyber_beta(model, "a") == pytest.approx(beta_c, abs=1e-12)
    # The effective beta of identical channels: 1 - (1 - beta_p)(1 - beta_c).
    assert common_cause_share(model, "a") == pytest.approx(combined_beta(beta_p, beta_c), abs=1e-12)
    assert total_rate(model, "a") == pytest.approx(LP + lc, rel=1e-12)


def test_cyber_rate_from_beta_validation() -> None:
    with pytest.raises(ValueError):
        cyber_rate_from_beta(LP, 1.0)
    assert cyber_beta_from_rates(0.0, 0.0) == 0.0


def test_a_diverse_channel_has_no_cyber_beta() -> None:
    _, b_same = group(2, 0.0, 1e-5, ["A", "A"])
    _, b_div = group(2, 0.0, 1e-5, ["A", "B"])
    assert b_same == pytest.approx(1e-5 / (LP + 1e-5))
    assert b_div == 0.0


# --- reductions --------------------------------------------------------------------------------


def test_zero_exposure_is_the_physical_model() -> None:
    physical = physical_ccf_model(mission_computers=2)
    zero = cyber_ccf_model(mission_computers=2, exposure_scale=0.0)
    assert len(zero.events) == len(physical.events)
    assert unreliability(zero, MISSION_HOURS) == unreliability(physical, MISSION_HOURS)


def test_identical_channels_collapse_to_one_event_per_attribute() -> None:
    model = cyber_ccf_model(mission_computers=2)
    egi_events = [e for e in model.causes["egi_1"] if e.startswith("cyber:")]
    assert sorted(egi_events) == sorted(
        cyber_event_name(d, v)
        for d, v in navigation_attributes(mission_computers=2)["egi_1"].items()
    )
    for e in egi_events:
        assert model.affected(e) == ["egi_1", "egi_2"]
        assert model.event(e).kind == "cyber_ccf"


def test_full_diversity_makes_cyber_failures_independent() -> None:
    full = {(g, d): 2 for g in ("nav_source", "mission_computer") for d in DIMENSIONS}
    model = cyber_ccf_model(mission_computers=2, distinct=full)
    cyber = [e for e in model.events if e.name.startswith("cyber:")]
    assert cyber and all(e.kind == "cyber_independent" for e in cyber)
    assert all(len(model.affected(e.name)) == 1 for e in cyber)
    assert cyber_beta(model, "egi_1") == 0.0


def test_shared_network_couples_the_groups() -> None:
    model = cyber_ccf_model(mission_computers=2, shared_network=True)
    event = cyber_event_name("network", "shared_net")
    assert model.affected(event) == ["egi_1", "egi_2", "mission_computer_1", "mission_computer_2"]


def test_attribute_validation() -> None:
    with pytest.raises(ValueError):
        navigation_attributes(distinct={("nav_source", "firmware"): 3})
    base = independent_model("g", Parallel("a", "b"), {"a": 1.0, "b": 1.0})
    with pytest.raises(ValueError, match="not a component"):
        apply_cyber(base, {"z": {"firmware": "A"}}, one_exposure(1.0))
    with pytest.raises(ValueError, match="no exposure"):
        apply_cyber(base, {"a": {"network": "A"}}, one_exposure(1.0))


@pytest.mark.parametrize("hours", [1.0, MISSION_HOURS, 100.0])
@pytest.mark.parametrize("mcs", [1, 2])
@pytest.mark.parametrize("shared_network", [False, True])
def test_identical_navigation_factors_out_every_cyber_event(
    hours: float, mcs: int, shared_network: bool
) -> None:
    # With identical attributes, every cyber event fails a whole redundant set (or a series
    # element), so it is a cut set of order one and factors out of the physical model exactly:
    # R = R_physical * prod over cyber events (1 - q_e).
    physical = physical_ccf_model(mission_computers=mcs)
    model = cyber_ccf_model(mission_computers=mcs, shared_network=shared_network)
    q = model.probabilities(hours)
    r = 1 - unreliability(physical, hours)
    for e in model.events:
        if e.name.startswith("cyber:"):
            r *= 1 - q[e.name]
    assert unreliability(model, hours) == pytest.approx(1 - r, rel=1e-12)


# --- properties -----------------------------------------------------------------------------------


@st.composite
def attribute_patterns(draw: st.DrawFn) -> tuple[int, list[str], list[str]]:
    """A group of m members and two firmware assignments, the second a refinement of the first."""
    m = draw(st.integers(2, 4))
    coarse = [draw(st.sampled_from("AB")) for _ in range(m)]
    fine = [c + draw(st.sampled_from("12")) for c in coarse]  # every class split further
    return m, coarse, fine


@settings(max_examples=150)
@given(attribute_patterns(), st.floats(0.0, 0.2), st.floats(0.0, 1e-2))
def test_diversifying_an_attribute_never_increases_unreliability(
    pattern: tuple[int, list[str], list[str]], beta_p: float, lc: float
) -> None:
    m, coarse, fine = pattern
    q_coarse, _ = group(m, beta_p, lc, coarse)
    q_fine, _ = group(m, beta_p, lc, fine)
    assert q_fine <= q_coarse + 1e-15


@settings(max_examples=100)
@given(st.floats(0.0, 10.0), st.floats(0.0, 10.0))
def test_more_exposure_never_helps(s1: float, s2: float) -> None:
    lo, hi = sorted((s1, s2))
    q_lo = unreliability(cyber_ccf_model(mission_computers=2, exposure_scale=lo), MISSION_HOURS)
    q_hi = unreliability(cyber_ccf_model(mission_computers=2, exposure_scale=hi), MISSION_HOURS)
    q_phys = unreliability(physical_ccf_model(mission_computers=2), MISSION_HOURS)
    assert q_phys <= q_lo + 1e-15 <= q_hi + 2e-15


@given(st.floats(0.0, 1.0), st.floats(0.0, 1.0), st.floats(0.0, 1.0), st.floats(0.0, 1.0))
def test_split_gain_is_the_exact_difference(k: float, a: float, b: float, c: float) -> None:
    # Two members, A = {x}, B = {y}; their other causes have probabilities a, b, plus a shared
    # other cause c (so U and V are dependent). Shared vs split event of probability k.
    names = ["x", "y"]
    base = independent_model("g", Parallel(*names), {"x": 1.0, "y": 1.0})
    shared = apply_cyber(
        apply_ccf(base, beta_group("o", names, 0.5)),
        {"x": {"firmware": "K"}, "y": {"firmware": "K"}},
        one_exposure(1.0),
    )
    split = apply_cyber(
        apply_ccf(base, beta_group("o", names, 0.5)),
        {"x": {"firmware": "K1"}, "y": {"firmware": "K2"}},
        one_exposure(1.0),
    )
    q_shared = {"x": a, "y": b, "o[x+y]": c, "cyber:firmware=K": k}
    q_split = {"x": a, "y": b, "o[x+y]": c, "cyber:firmware=K1": k, "cyber:firmware=K2": k}
    p_u, p_v = 1 - (1 - a) * (1 - c), 1 - (1 - b) * (1 - c)
    p_uv = c + (1 - c) * a * b
    drop = failure_probability(shared, q_shared) - failure_probability(split, q_split)
    assert drop == pytest.approx(split_gain(k, p_u, p_v, p_uv), abs=1e-12)
    assert drop >= -1e-15


def test_a_single_computer_gains_only_its_own_exposure() -> None:
    # One mission computer is a series element: its cyber events add to its failure rate and
    # are not common cause. Its exposure is the sum of the three attribute rates.
    model = cyber_ccf_model()
    exp = load_exposures()
    expected = 5e-5 + sum(e.rate_per_hour for e in exp.values())
    assert total_rate(model, "mission_computer") == pytest.approx(expected, rel=1e-12)
    assert all(
        model.event(e).kind == "cyber_independent"
        for e in model.causes["mission_computer"]
        if e.startswith("cyber:")
    )


def test_cyber_can_lower_series_unreliability_too() -> None:
    # The same caveat as for physical CCF: in series, sharing an event wastes it.
    names = ["a", "b"]
    m = independent_model("s", Series(*names), dict.fromkeys(names, 1e-3))
    shared = apply_cyber(m, {n: {"firmware": "A"} for n in names}, one_exposure(1e-2))
    split = apply_cyber(m, {"a": {"firmware": "A"}, "b": {"firmware": "B"}}, one_exposure(1e-2))
    assert unreliability(shared, 10.0) < unreliability(split, 10.0)
    assert math.isfinite(unreliability(shared, 10.0))
