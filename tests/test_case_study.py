"""Phase 5: the case study's numbers against hand-derived closed forms."""

from __future__ import annotations

import math

import pytest

from cyberccf.architecture_diversity_tradeoff import cost, make_architecture
from cyberccf.case_study_application import (
    EXPOSURE_RANGE,
    REDUNDANT,
    REQUIREMENT,
    SINGLE_STRING,
    recommend,
    tornado,
    unreliability_with,
    views,
)
from cyberccf.cyber_ccf_model import DIMENSIONS, cyber_ccf_model, load_exposures
from cyberccf.independence_baseline import MISSION_HOURS, unreliability
from cyberccf.physical_ccf_beta_factor import beta_split, load_ccf_parameters

T = MISSION_HOURS


def q(rate: float) -> float:
    return -math.expm1(-rate * T)


def hand_derived(cyber_scale: float, with_ccf: bool) -> float:
    """Two EGIs, two bus channels, two mission computers, identical attributes.

    Conditioning on the power buses (Lesson 1) gives the independent part; each common-cause
    event is an order-one cut set and factors out (Proposition 8 of docs/derivation.md).
    """
    b = load_ccf_parameters()
    beta = {g: (r.beta if with_ccf else 0.0) for g, r in b.items()}
    qi_e, qc_e = beta_split(2e-4, beta["nav_source"], T)
    qi_p, qc_p = beta_split(2e-5, beta["power"], T)
    qi_b, qc_b = beta_split(1e-5, beta["data_bus"], T)
    qi_m, qc_m = beta_split(5e-5, beta["mission_computer"], T)
    sources = (1 - qi_p) ** 2 * (1 - qi_e**2) + 2 * qi_p * (1 - qi_p) * (1 - qi_e)
    r = (1 - qi_b**2) * (1 - qi_m**2) * sources
    r *= (1 - qc_e) * (1 - qc_p) * (1 - qc_b) * (1 - qc_m)
    exp = load_exposures()
    for _group in ("nav_source", "mission_computer"):  # one event per attribute per group
        for d in DIMENSIONS:
            r *= 1 - q(cyber_scale * exp[d].rate_per_hour)
    return 1 - r


def test_the_three_numbers_match_hand_derived_closed_forms() -> None:
    v = views(REDUNDANT)
    assert v.as_claimed == pytest.approx(hand_derived(0.0, with_ccf=False), rel=1e-12)
    assert v.physical == pytest.approx(hand_derived(0.0, with_ccf=True), rel=1e-12)
    assert v.cyber == pytest.approx(hand_derived(1.0, with_ccf=True), rel=1e-12)
    lo, hi = EXPOSURE_RANGE
    assert v.cyber_low == pytest.approx(hand_derived(lo, with_ccf=True), rel=1e-12)
    assert v.cyber_high == pytest.approx(hand_derived(hi, with_ccf=True), rel=1e-12)


@pytest.mark.parametrize(
    "arch", [REDUNDANT, SINGLE_STRING, make_architecture(3, 2, {("nav_source", "firmware"): 3})]
)
def test_ordering_as_claimed_physical_cyber(arch: object) -> None:
    v = views(arch)  # type: ignore[arg-type]
    assert v.as_claimed <= v.physical <= v.cyber_low <= v.cyber <= v.cyber_high


def test_single_string_has_no_redundant_group_but_power() -> None:
    v = views(SINGLE_STRING, bus_channels=1)
    assert "1 bus channel" in v.label
    # Only the power pair is redundant, so physical CCF changes little; cyber adds exposure.
    assert v.physical / v.as_claimed < 1.05
    assert v.cyber > v.physical


def test_unreliability_with_unit_factor_is_unreliability() -> None:
    m = cyber_ccf_model(mission_computers=2)
    assert unreliability_with(m, T, lambda e: 1.0) == pytest.approx(unreliability(m, T), rel=1e-14)
    with pytest.raises(ValueError):
        unreliability_with(m, T, lambda e: -1.0)


def test_tornado_bars_are_sorted_and_consistent() -> None:
    bars = tornado()
    assert [b.swing for b in bars] == sorted((b.swing for b in bars), reverse=True)
    assert len(bars) == 4 + 4 + len(DIMENSIONS)
    base = unreliability(cyber_ccf_model(mission_computers=2), T)
    for b in bars:
        # Every parameter makes things worse as it grows, so low <= base <= high, except the
        # beta ranges, whose table value sits inside the range.
        assert b.q_low <= base * (1 + 1e-12) or b.parameter.startswith("β")
        assert b.q_high >= b.q_low
    firmware = next(b for b in bars if b.parameter == "firmware exposure")
    # Removing the firmware exposure removes exactly the two firmware events (factorisation).
    exp = load_exposures()["firmware"].rate_per_hour
    assert 1 - firmware.q_low == pytest.approx((1 - base) / (1 - q(exp)) ** 2, rel=1e-12)


def test_recommendation_is_the_cheapest_design_that_meets_the_requirement() -> None:
    candidates = [
        make_architecture(2, 2),
        make_architecture(3, 2),
        make_architecture(
            2, 2, {(g, d): 2 for g in ("nav_source", "mission_computer") for d in DIMENSIONS}
        ),
    ]
    rec = recommend(candidates=candidates)
    assert rec is not None
    assert rec.architecture == candidates[2]
    assert rec.q_worst <= REQUIREMENT < rec.q_worst * 100
    assert rec.cost == cost(candidates[2])
    assert recommend(requirement=1e-9, candidates=candidates) is None
