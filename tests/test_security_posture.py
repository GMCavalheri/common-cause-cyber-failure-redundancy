"""Extra: the posture rubric is transcribed faithfully, monotone and always a valid range."""

from __future__ import annotations

import math

import pytest

from cyberccf.architecture_diversity_tradeoff import make_architecture
from cyberccf.case_study_application import REDUNDANT
from cyberccf.cyber_ccf_model import DIMENSIONS, cyber_ccf_model
from cyberccf.independence_baseline import MISSION_HOURS, unreliability
from cyberccf.security_posture import (
    LEVELS,
    controls_at,
    cyber_beta_range,
    decades,
    exposure_range,
    load_controls,
    load_rubric,
    unreliability_range,
)

FULL = make_architecture(
    2, 2, {(g, d): 2 for g in ("nav_source", "mission_computer") for d in DIMENSIONS}
)


def test_controls_are_transcribed_from_the_overlay() -> None:
    controls = load_controls()
    assert all("NIST SP 800" in c.source for c in controls)
    by_id = {c.control: c for c in controls}
    # Spot checks against NIST SP 800-82r3 Appendix F, Table 22.
    assert (by_id["SC-7(29)"].low, by_id["SC-7(29)"].moderate, by_id["SC-7(29)"].high) == (
        True,
        True,
        True,
    )
    assert (by_id["SC-7(21)"].low, by_id["SC-7(21)"].moderate, by_id["SC-7(21)"].high) == (
        False,
        False,
        True,
    )
    assert (by_id["SI-7"].low, by_id["SI-7"].moderate) == (False, True)
    assert by_id["SR-9"].high and not by_id["SR-9"].moderate
    # SC-29 Heterogeneity: selected in no baseline, acts on no attribute here.
    sc29 = by_id["SC-29"]
    assert not (sc29.low or sc29.moderate or sc29.high)
    assert sc29.dimension == "none"


def test_levels_are_nested() -> None:
    # Every control selected at a level is selected at every higher level.
    for c in load_controls():
        assert c.low <= c.moderate <= c.high
    for d in DIMENSIONS:
        counts = [len(controls_at(level, d)) for level in LEVELS]
        assert counts == sorted(counts)
        assert counts[0] == 0
    with pytest.raises(ValueError):
        load_controls()[0].selected("extreme")


def test_rubric_parameters_are_labelled_and_sane() -> None:
    r = load_rubric()
    assert 0 < r.effect_low <= r.effect_high < 1
    assert 0 < r.unprotected_low < 1 < r.unprotected_high


@pytest.mark.parametrize("level", LEVELS)
def test_ranges_are_valid(level: str) -> None:
    for lo, hi in exposure_range(level).values():
        assert 0 < lo <= hi
    b_lo, b_hi = cyber_beta_range(level, 2e-4)
    assert 0 < b_lo <= b_hi < 1
    q_lo, q_hi = unreliability_range(REDUNDANT, level)
    assert 0 < q_lo <= q_hi < 1


def test_a_stronger_posture_never_raises_the_range() -> None:
    previous = None
    for level in LEVELS:
        rng = exposure_range(level)
        beta = cyber_beta_range(level, 2e-4)
        q = unreliability_range(REDUNDANT, level)
        if previous is not None:
            p_rng, p_beta, p_q = previous
            for d in DIMENSIONS:
                assert rng[d][0] <= p_rng[d][0] and rng[d][1] <= p_rng[d][1]
            assert beta[0] <= p_beta[0] and beta[1] <= p_beta[1]
            assert q[0] <= p_q[0] * (1 + 1e-12) and q[1] <= p_q[1] * (1 + 1e-12)
        previous = (rng, beta, q)


def test_no_posture_has_exposure_one_closed_form() -> None:
    # With no controls the interval is exactly the unprotected scale.
    r = load_rubric()
    for lo, hi in exposure_range("none").values():
        assert (lo, hi) == (r.unprotected_low, r.unprotected_high)
    # And the corners equal rebuilding the model at those uniform scales.
    q_lo, q_hi = unreliability_range(REDUNDANT, "none")
    m_lo = cyber_ccf_model(mission_computers=2, exposure_scale=r.unprotected_low)
    m_hi = cyber_ccf_model(mission_computers=2, exposure_scale=r.unprotected_high)
    assert q_lo == pytest.approx(unreliability(m_lo, MISSION_HOURS), rel=1e-12)
    assert q_hi == pytest.approx(unreliability(m_hi, MISSION_HOURS), rel=1e-12)


def test_n_controls_multiply_by_one_minus_f_to_the_n() -> None:
    r = load_rubric()
    n = len(controls_at("high", "firmware"))
    lo, hi = exposure_range("high")["firmware"]
    assert lo == pytest.approx(r.unprotected_low * (1 - r.effect_high) ** n, rel=1e-14)
    assert hi == pytest.approx(r.unprotected_high * (1 - r.effect_low) ** n, rel=1e-14)


def test_diversity_beats_posture_at_the_worst_case() -> None:
    # The diverse design with no controls at all is, at its worst corner, better than the
    # identical design at the high level's worst corner: posture lowers exposure, diversity
    # removes sharing.
    assert unreliability_range(FULL, "none")[1] < unreliability_range(REDUNDANT, "high")[1]
    assert decades(1.0, 10.0) == pytest.approx(1.0)
    assert math.isfinite(decades(*unreliability_range(REDUNDANT, "moderate")))
