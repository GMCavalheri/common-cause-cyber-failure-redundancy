"""Phase 2: physical common cause against NUREG/CR-5485, closed forms and properties."""

from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cyberccf.independence_baseline import (
    MISSION_HOURS,
    BasicEvent,
    KofN,
    Model,
    Parallel,
    Series,
    failure_probability,
    independent_model,
    navigation_model,
    navigation_unreliability,
    unreliability,
)
from cyberccf.physical_ccf_beta_factor import (
    CCFGroup,
    alpha_fractions,
    alphas_from_fractions,
    apply_ccf,
    beta_equivalent,
    beta_factor_fractions,
    beta_group,
    beta_split,
    ccf_event_name,
    ccf_floor,
    check_fractions,
    independent_fractions,
    load_ccf_parameters,
    mgl_fractions,
    one_of_m_beta_unreliability,
    physical_ccf_model,
    two_of_three_rare_event,
)

unit = st.floats(0.0, 1.0, allow_nan=False)


@st.composite
def alpha_vectors(draw: st.DrawFn, m: int) -> list[float]:
    raw = [draw(st.floats(0.0, 1.0)) for _ in range(m)]
    if sum(raw) == 0:
        raw[0] = 1.0
    return [x / sum(raw) for x in raw]


# --- the parametric models ------------------------------------------------------------------


@given(st.integers(2, 6), st.data())
def test_every_model_conserves_the_total_failure_probability(m: int, data: st.DataObject) -> None:
    # NUREG/CR-5485: Q_t = sum_k C(m-1, k-1) Q_k for every parametric model.
    check_fractions(m, beta_factor_fractions(m, data.draw(unit)))
    check_fractions(m, mgl_fractions(m, [data.draw(unit) for _ in range(m - 1)]))
    alphas = data.draw(alpha_vectors(m))
    check_fractions(m, alpha_fractions(m, alphas, staggered=True))
    check_fractions(m, alpha_fractions(m, alphas, staggered=False))
    check_fractions(m, independent_fractions(m))


def test_mgl_three_components_is_nureg_eq_5_11() -> None:
    # NUREG/CR-5485 Eq. 5.11: Q1 = (1 - beta) Qt, Q2 = 1/2 beta (1 - gamma) Qt, Q3 = beta gamma Qt.
    beta, gamma = 0.1, 0.3
    assert mgl_fractions(3, [beta, gamma]) == pytest.approx(
        [1 - beta, 0.5 * beta * (1 - gamma), beta * gamma], rel=1e-15
    )


def test_staggered_alpha_three_components_is_nureg_eq_5_10() -> None:
    # NUREG/CR-5485 example before Eq. 5.10: Q1 = a1 Qt, Q2 = a2/2 Qt, Q3 = a3 Qt.
    a = [0.95, 0.03, 0.02]
    assert alpha_fractions(3, a, staggered=True) == pytest.approx([0.95, 0.015, 0.02], rel=1e-15)


def test_non_staggered_alpha_is_nureg_eq_5_7() -> None:
    # NUREG/CR-5485 Eq. 5.7: Q_k = k / C(m-1, k-1) * alpha_k / alpha_t * Q_t.
    a = [0.9, 0.06, 0.03, 0.01]
    at = sum(k * x for k, x in enumerate(a, start=1))
    expected = [k / math.comb(3, k - 1) * x / at for k, x in enumerate(a, start=1)]
    assert alpha_fractions(4, a, staggered=False) == pytest.approx(expected, rel=1e-15)


def test_beta_is_mgl_with_further_letters_one() -> None:
    for m in range(2, 6):
        assert mgl_fractions(m, [0.07] + [1.0] * (m - 2)) == pytest.approx(
            beta_factor_fractions(m, 0.07), abs=1e-15
        )


def test_two_member_models_coincide() -> None:
    # For m = 2 the MGL beta, the staggered alpha_2 and the beta factor are the same number.
    assert alpha_fractions(2, [0.95, 0.05], staggered=True) == pytest.approx(
        beta_factor_fractions(2, 0.05)
    )
    # Non-staggered: beta = 2 a2 / (a1 + 2 a2).
    f = alpha_fractions(2, [0.95, 0.05], staggered=False)
    assert beta_equivalent(2, f) == pytest.approx(2 * 0.05 / (0.95 + 2 * 0.05), rel=1e-15)


@given(st.integers(2, 6), st.booleans(), st.data())
def test_alpha_round_trip(m: int, staggered: bool, data: st.DataObject) -> None:
    alphas = data.draw(alpha_vectors(m))
    back = alphas_from_fractions(m, alpha_fractions(m, alphas, staggered), staggered)
    assert back == pytest.approx(alphas, abs=1e-12)


def test_parametric_validation() -> None:
    with pytest.raises(ValueError):
        beta_factor_fractions(1, 0.1)
    with pytest.raises(ValueError):
        beta_factor_fractions(2, 1.5)
    with pytest.raises(ValueError):
        mgl_fractions(1, [])
    with pytest.raises(ValueError):
        mgl_fractions(3, [0.1])
    with pytest.raises(ValueError):
        alpha_fractions(2, [0.5], staggered=True)
    with pytest.raises(ValueError):
        alpha_fractions(2, [0.5, 0.6], staggered=True)
    with pytest.raises(ValueError):
        check_fractions(2, [1.0])
    with pytest.raises(ValueError):
        check_fractions(2, [-0.1, 0.55])
    with pytest.raises(ValueError):
        check_fractions(2, [0.5, 0.1])


# --- NUREG/CR-5485 Tables 5-4 and 5-5: CCF contributions to k-of-m systems ------------------

QT = 1e-7  # small enough that the rare-event sums of the tables are exact to ~1e-6 relative

# (m, k_success): the CCF-only failure probability / QT, staggered (Table 5-4) and
# non-staggered (Table 5-5, divided by alpha_t there).
STAGGERED = {
    (2, 1): lambda a: a[1],
    (3, 1): lambda a: a[2],
    (3, 2): lambda a: 3 * a[1] / 2 + a[2],
    (4, 1): lambda a: a[3],
    (4, 2): lambda a: 4 * a[2] / 3 + a[3],
    (4, 3): lambda a: 4 * a[1] / 2 + 4 * a[2] / 3 + a[3],
    (5, 2): lambda a: 5 * a[3] / 4 + a[4],
}
NON_STAGGERED = {
    (2, 1): lambda a: 2 * a[1],
    (3, 1): lambda a: 3 * a[2],
    (3, 2): lambda a: 3 * (a[1] + a[2]),
    (4, 1): lambda a: 4 * a[3],
    (4, 2): lambda a: 4 * (a[2] + a[3]),
    (4, 3): lambda a: 4 * (a[1] + a[2] + a[3]),
}


def ccf_only_failure(m: int, k: int, fractions: list[float]) -> float:
    """Exact P(k-of-m system fails) from the CCF events alone (independent part switched off)."""
    names = [f"c{i}" for i in range(m)]
    model = apply_ccf(
        independent_model("t", KofN(k, *names), dict.fromkeys(names, 1.0)),
        CCFGroup("g", tuple(names), tuple(fractions)),
    )
    q = {}
    for e in model.events:
        size = 1 if e.kind == "independent" else e.name.count("+") + 1
        q[e.name] = 0.0 if size == 1 else fractions[size - 1] * QT
    return failure_probability(model, q)


@pytest.mark.parametrize(("m", "k"), list(STAGGERED))
def test_table_5_4_staggered(m: int, k: int) -> None:
    a = [0.9, 0.05, 0.03, 0.015, 0.005][:m]
    a = [x / sum(a) for x in a]
    got = ccf_only_failure(m, k, alpha_fractions(m, a, staggered=True))
    assert got == pytest.approx(STAGGERED[(m, k)](a) * QT, rel=1e-5)


@pytest.mark.parametrize(("m", "k"), list(NON_STAGGERED))
def test_table_5_5_non_staggered(m: int, k: int) -> None:
    a = [0.9, 0.05, 0.03, 0.02][:m]
    a = [x / sum(a) for x in a]
    at = sum(j * x for j, x in enumerate(a, start=1))
    got = ccf_only_failure(m, k, alpha_fractions(m, a, staggered=False))
    assert got == pytest.approx(NON_STAGGERED[(m, k)](a) / at * QT, rel=1e-5)


def test_two_of_three_matches_nureg_eq_5_5() -> None:
    # Eq. 5.5 is the rare-event approximation; the exact value differs by higher-order terms.
    f = mgl_fractions(3, [0.1, 0.3])
    qt = 1e-4
    names = ["a", "b", "c"]
    model = apply_ccf(
        independent_model("t", KofN(2, *names), dict.fromkeys(names, 1.0)),
        CCFGroup("g", tuple(names), tuple(f)),
    )
    q = {e.name: f[e.name.count("+")] * qt if "[" in e.name else f[0] * qt for e in model.events}
    exact = failure_probability(model, q)
    approx = two_of_three_rare_event(f[0] * qt, f[1] * qt, f[2] * qt)
    assert exact == pytest.approx(approx, rel=1e-3)
    assert exact <= approx  # the rare-event sum over-counts overlaps


# --- groups as shared basic events --------------------------------------------------------------


def test_apply_ccf_builds_one_event_per_subset() -> None:
    names = ["a", "b", "c"]
    base = independent_model("t", Parallel(*names), dict.fromkeys(names, 1e-3))
    model = apply_ccf(base, CCFGroup("g", tuple(names), tuple(mgl_fractions(3, [0.1, 0.5]))))
    ccf = [e for e in model.events if e.kind == "physical_ccf"]
    assert len(ccf) == 3 + 1  # three pairs and the triple
    pair = model.event(ccf_event_name("g", ("a", "b")))
    assert pair.rate_per_hour == pytest.approx(0.5 * 0.1 * 0.5 * 1e-3)
    assert model.affected(pair.name) == ["a", "b"]


@settings(max_examples=100)
@given(st.integers(2, 4), unit, unit, st.floats(1e-6, 1e-2), st.floats(0.1, 1000.0))
def test_a_members_total_failure_probability_is_unchanged(
    m: int, beta: float, gamma: float, rate: float, hours: float
) -> None:
    # Common cause moves probability between cut sets; each component still fails with
    # 1 - exp(-lambda_t t), because its events are independent Poisson processes.
    names = [f"c{i}" for i in range(m)]
    letters = [beta] + [gamma] * (m - 2)
    model = apply_ccf(
        independent_model("t", Parallel(*names), dict.fromkeys(names, rate)),
        CCFGroup("g", tuple(names), tuple(mgl_fractions(m, letters))),
    )
    q = model.probabilities(hours)
    for c in names:
        survive = math.prod(1 - q[e] for e in model.causes[c])
        assert 1 - survive == pytest.approx(-math.expm1(-rate * hours), rel=1e-9)


def test_beta_zero_reduces_to_independence_exactly() -> None:
    base = navigation_model(mission_computers=2)
    zero = physical_ccf_model(
        mission_computers=2,
        betas=dict.fromkeys(("nav_source", "data_bus", "power", "mission_computer"), 0.0),
    )
    assert unreliability(zero, MISSION_HOURS) == unreliability(base, MISSION_HOURS)
    # A group whose beta is zero adds no events at all; one with beta = 0 explicitly is a no-op.
    names = ["a", "b"]
    m = independent_model("t", Parallel(*names), dict.fromkeys(names, 1e-3))
    assert unreliability(apply_ccf(m, beta_group("g", names, 0.0)), 10.0) == unreliability(m, 10.0)


@pytest.mark.parametrize("m", [2, 3, 4, 6])
@pytest.mark.parametrize("beta", [0.0, 0.01, 0.1, 1.0])
def test_one_of_m_closed_form(m: int, beta: float) -> None:
    names = [f"c{i}" for i in range(m)]
    model = apply_ccf(
        independent_model("t", Parallel(*names), dict.fromkeys(names, 2e-4)),
        beta_group("g", names, beta),
    )
    assert unreliability(model, MISSION_HOURS) == pytest.approx(
        one_of_m_beta_unreliability(m, 2e-4, beta, MISSION_HOURS), rel=1e-12, abs=1e-300
    )


def test_identical_redundancy_cannot_beat_the_ccf_floor() -> None:
    floor = ccf_floor(2e-4, 0.05, MISSION_HOURS)
    values = [one_of_m_beta_unreliability(m, 2e-4, 0.05, MISSION_HOURS) for m in range(1, 9)]
    assert all(v >= floor for v in values)
    assert values[-1] == pytest.approx(floor, rel=1e-12)
    q_i, q_c = beta_split(2e-4, 0.05, MISSION_HOURS)
    assert q_c == floor
    assert 1 - (1 - q_i) * (1 - q_c) == pytest.approx(-math.expm1(-2e-3), rel=1e-12)


def test_apply_ccf_validation() -> None:
    names = ["a", "b"]
    m = independent_model("t", Parallel(*names), {"a": 1e-3, "b": 2e-3})
    with pytest.raises(ValueError, match="different rates"):
        apply_ccf(m, beta_group("g", names, 0.1))
    with pytest.raises(ValueError, match="not a component"):
        apply_ccf(m, beta_group("g", ["a", "z"], 0.1))
    with pytest.raises(ValueError):
        CCFGroup("g", ("a",), (1.0,))
    same = independent_model("t", Parallel(*names), dict.fromkeys(names, 1e-3))
    once = apply_ccf(same, beta_group("g", names, 0.1))
    shared_twice = Model(
        "x",
        once.structure,
        (*once.events, BasicEvent("extra", 1e-3)),
        {"a": (*once.causes["a"], "extra"), "b": once.causes["b"]},
    )
    with pytest.raises(ValueError, match="exactly one independent"):
        apply_ccf(shared_twice, beta_group("h", names, 0.1))


# --- directionality (the PLAN's validation check) ------------------------------------------------


@st.composite
def redundant_group_in_a_system(draw: st.DrawFn) -> tuple[Model, CCFGroup]:
    """A parallel group of m identical members inside a random series/parallel context."""
    m = draw(st.integers(2, 4))
    members = [f"g{i}" for i in range(m)]
    others = [f"o{i}" for i in range(draw(st.integers(0, 3)))]
    group_block = Parallel(*members)
    shape = draw(st.sampled_from(["alone", "series", "parallel", "nested"]))
    if not others or shape == "alone":
        structure = group_block
    elif shape == "series":
        structure = Series(group_block, *others)
    elif shape == "parallel":
        structure = Parallel(group_block, *others)
    else:
        structure = Series(Parallel(group_block, others[0]), *others[1:])
    rate = draw(st.floats(1e-5, 1e-1))
    rates = dict.fromkeys(members, rate) | {o: draw(st.floats(0.0, 1e-1)) for o in others}
    letters = [draw(unit) for _ in range(m - 1)]
    group = CCFGroup("g", tuple(members), tuple(mgl_fractions(m, letters)))
    return independent_model("r", structure, rates), group


@settings(max_examples=200)
@given(redundant_group_in_a_system(), st.floats(0.1, 100.0))
def test_ccf_on_a_redundant_group_never_improves_reliability(
    mg: tuple[Model, CCFGroup], hours: float
) -> None:
    # The members' failures become positively associated (Esary, Proschan & Walkup, 1967) with
    # unchanged marginals, so P(all members fail) can only rise, and the system is monotone in
    # that block. This is the PLAN's check: CCF-adjusted reliability <= independence estimate.
    model, group = mg
    with_ccf = apply_ccf(model, group)
    assert unreliability(with_ccf, hours) >= unreliability(model, hours) - 1e-15


def test_ccf_on_a_series_group_lowers_unreliability() -> None:
    # The directionality check holds for *redundant* groups only. In series, failures that
    # coincide waste each other: P(at least one fails) falls when they are associated.
    names = ["a", "b"]
    series = independent_model("s", Series(*names), dict.fromkeys(names, 1e-2))
    with_ccf = apply_ccf(series, beta_group("g", names, 0.5))
    assert unreliability(with_ccf, 10.0) < unreliability(series, 10.0)


# --- the navigation system ------------------------------------------------------------------------


def test_ccf_parameters_are_labelled() -> None:
    rows = load_ccf_parameters()
    assert set(rows) == {"nav_source", "data_bus", "power", "mission_computer"}
    for r in rows.values():
        assert "assumption" in r.basis and "IEC 61508-6" in r.basis
        lo, hi = (0.005, 0.05) if "programmable" in r.basis else (0.01, 0.1)
        assert lo <= r.beta <= hi


@pytest.mark.parametrize("hours", [1.0, MISSION_HOURS, 1000.0])
def test_navigation_with_beta_matches_hand_derived_closed_form(hours: float) -> None:
    # A CCF event of a redundant set fails the whole set, so it is a cut set of order one and
    # factors out: R = R_independent(q_i's) * (1 - q_c,egi)(1 - q_c,bus)(1 - q_c,power).
    rows = load_ccf_parameters()
    model = physical_ccf_model()
    qi_e, qc_e = beta_split(2e-4, rows["nav_source"].beta, hours)
    qi_p, qc_p = beta_split(2e-5, rows["power"].beta, hours)
    qi_b, qc_b = beta_split(1e-5, rows["data_bus"].beta, hours)
    q_m = -math.expm1(-5e-5 * hours)
    r = (1 - navigation_unreliability(qi_e, qi_p, qi_b, q_m)) * (1 - qc_e) * (1 - qc_p) * (1 - qc_b)
    assert unreliability(model, hours) == pytest.approx(1 - r, rel=1e-12)


def test_navigation_groups_follow_the_redundancy() -> None:
    single = physical_ccf_model()
    dual = physical_ccf_model(mission_computers=2)

    def kinds(m: Model) -> list[str]:
        return sorted({e.name.split("[")[0] for e in m.events if e.kind == "physical_ccf"})

    assert kinds(single) == ["bus_ccf", "egi_ccf", "power_ccf"]
    assert kinds(dual) == ["bus_ccf", "egi_ccf", "mc_ccf", "power_ccf"]
    triple = physical_ccf_model(egi_units=3)
    assert len([e for e in triple.events if e.name.startswith("egi_ccf")]) == 1  # beta: one event
    assert unreliability(dual, MISSION_HOURS) > unreliability(
        navigation_model(mission_computers=2), MISSION_HOURS
    )


def test_ccf_event_names_are_stable() -> None:
    assert ccf_event_name("g", ("a", "b")) == "g[a+b]"
