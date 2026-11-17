"""Phase 1: the independence baseline against closed forms and a brute-force oracle."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from cyberccf.independence_baseline import (
    MISSION_HOURS,
    BasicEvent,
    KofN,
    KOutOfN,
    Model,
    Parallel,
    Series,
    at_least_k,
    component_specs,
    describe,
    enumerate_failure_probability,
    failure_probability,
    independent_model,
    k_of_n_reliability,
    leaves,
    load_parameters,
    minimal_cut_sets,
    navigation_model,
    navigation_unreliability,
    one_of_n_unreliability,
    parallel_unreliability,
    series_unreliability,
    shared_events,
    unreliability,
)

probs = st.floats(0.0, 1.0, allow_nan=False)


def model_from_q(structure: KOutOfN, q: dict[str, float]) -> Model:
    return independent_model("t", structure, dict.fromkeys(q, 1.0))


# --- structure ---------------------------------------------------------------------------


def test_block_validation() -> None:
    with pytest.raises(ValueError):
        KOutOfN(1, ())
    with pytest.raises(ValueError):
        KofN(3, "a", "b")


def test_leaves_keep_repeats_and_describe() -> None:
    s = Series(Parallel("a", "b"), KofN(2, "a", "c", "d"), Series("e"))
    assert leaves(s) == ["a", "b", "a", "c", "d", "e"]
    assert describe(s) == "series(parallel(a, b), 2-of-3(a, c, d), e)"


@given(st.lists(probs, min_size=1, max_size=6), st.data())
def test_at_least_k_matches_enumeration(p: list[float], data: st.DataObject) -> None:
    # Oracle: sum over all 2**n work/fail patterns with at least k working children.
    from itertools import product

    k = data.draw(st.integers(1, len(p)))
    total = 0.0
    for pattern in product((0, 1), repeat=len(p)):
        if sum(pattern) >= k:
            total += math.prod(pi if s else 1 - pi for pi, s in zip(p, pattern, strict=True))
    assert at_least_k(k, p) == pytest.approx(total, abs=1e-12)


# --- closed forms --------------------------------------------------------------------------


@given(st.lists(probs, min_size=1, max_size=5))
def test_series_and_parallel_closed_forms(q: list[float]) -> None:
    names = {f"c{i}": qi for i, qi in enumerate(q)}
    series = model_from_q(Series(*names), names)
    parallel = model_from_q(Parallel(*names), names)
    assert failure_probability(series, names) == pytest.approx(series_unreliability(q), abs=1e-12)
    assert failure_probability(parallel, names) == pytest.approx(
        parallel_unreliability(q), abs=1e-12
    )


@pytest.mark.parametrize(("k", "n"), [(1, 1), (1, 3), (2, 3), (3, 3), (2, 4), (3, 5)])
@pytest.mark.parametrize("p", [0.0, 0.3, 0.9, 1.0])
def test_k_of_n_matches_binomial_tail(k: int, n: int, p: float) -> None:
    q = {f"c{i}": 1 - p for i in range(n)}
    m = model_from_q(KofN(k, *q), q)
    assert 1 - failure_probability(m, q) == pytest.approx(k_of_n_reliability(k, n, p), abs=1e-12)


def test_one_of_n_is_q_to_the_n() -> None:
    for n in range(1, 5):
        q = dict.fromkeys((f"c{i}" for i in range(n)), 0.1)
        m = model_from_q(Parallel(*q), q)
        assert failure_probability(m, q) == pytest.approx(one_of_n_unreliability(n, 0.1), rel=1e-12)


# --- events and the model -------------------------------------------------------------------


def test_event_probability_is_one_minus_exp() -> None:
    e = BasicEvent("x", 2e-4)
    assert e.probability(10.0) == pytest.approx(1 - math.exp(-2e-3), rel=1e-14)
    assert e.probability(0.0) == 0.0
    with pytest.raises(ValueError):
        e.probability(-1.0)


@pytest.mark.parametrize(
    "kwargs",
    [{"rate_per_hour": -1.0}, {"rate_per_hour": math.inf}, {"rate_per_hour": 1.0, "kind": "x"}],
)
def test_event_validation(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        BasicEvent("x", **kwargs)  # type: ignore[arg-type]


def test_model_validation() -> None:
    e = BasicEvent("a", 1.0)
    with pytest.raises(ValueError, match="unique"):
        Model("m", "a", (e, e), {"a": ("a",)})
    with pytest.raises(ValueError, match="no basic event"):
        Model("m", "a", (e,), {})
    with pytest.raises(ValueError, match="unknown"):
        Model("m", "a", (e,), {"a": ("b",)})
    with pytest.raises(ValueError, match="not in the structure"):
        Model("m", "a", (e,), {"a": ("a",), "z": ("a",)})
    m = Model("m", "a", (e,), {"a": ("a",)})
    assert m.event("a") is e
    with pytest.raises(KeyError):
        m.event("b")
    with pytest.raises(ValueError):
        failure_probability(m, {"a": 1.5})


def test_shared_events_are_the_repeated_leaves() -> None:
    m = navigation_model()
    assert shared_events(m) == ["power_bus_1", "power_bus_2"]


@st.composite
def random_models(draw: st.DrawFn) -> tuple[Model, dict[str, float]]:
    """Random block diagrams over a few components with shared leaves and shared events."""
    comps = [f"c{i}" for i in range(draw(st.integers(2, 5)))]

    def block(depth: int) -> KOutOfN | str:
        if depth == 0 or draw(st.booleans()):
            return draw(st.sampled_from(comps))
        children = [block(depth - 1) for _ in range(draw(st.integers(1, 3)))]
        return KOutOfN(draw(st.integers(1, len(children))), tuple(children))

    structure = KOutOfN(1, (block(3), block(3)))
    used = list(dict.fromkeys(leaves(structure)))
    events = [BasicEvent(f"e_{c}", 1.0) for c in used]
    causes = {c: [f"e_{c}"] for c in used}
    for j in range(draw(st.integers(0, 2))):  # common-cause events shared by several components
        members = draw(st.lists(st.sampled_from(used), min_size=1, unique=True))
        events.append(BasicEvent(f"s{j}", 1.0, "physical_ccf"))
        for c in members:
            causes[c].append(f"s{j}")
    q = {e.name: draw(probs) for e in events}
    return Model("r", structure, tuple(events), {c: tuple(v) for c, v in causes.items()}), q


@settings(max_examples=200)
@given(random_models())
def test_factoring_equals_brute_force_enumeration(mq: tuple[Model, dict[str, float]]) -> None:
    model, q = mq
    assert failure_probability(model, q) == pytest.approx(
        enumerate_failure_probability(model, q), abs=1e-12
    )


@given(st.integers(1, 4), st.floats(0.0, 1.0), st.floats(0.0, 1.0))
def test_adding_a_redundant_channel_never_lowers_reliability(
    n: int, q_channel: float, q_rest: float
) -> None:
    q = {f"c{i}": q_channel for i in range(n)} | {"rest": q_rest}
    q_more = q | {f"c{n}": q_channel}
    fewer = model_from_q(Series(Parallel(*(f"c{i}" for i in range(n))), "rest"), q)
    more = model_from_q(Series(Parallel(*(f"c{i}" for i in range(n + 1))), "rest"), q_more)
    assert failure_probability(more, q_more) <= failure_probability(fewer, q) + 1e-15


def test_enumeration_refuses_huge_models() -> None:
    q = {f"c{i}": 0.1 for i in range(23)}
    with pytest.raises(ValueError):
        enumerate_failure_probability(model_from_q(Parallel(*q), q), q)


def test_minimal_cut_sets_of_the_navigation_system() -> None:
    cuts = {tuple(sorted(c)) for c in minimal_cut_sets(navigation_model())}
    # Hand-derived: the mission computer alone, both power buses, both bus channels, both EGIs,
    # and each EGI with the other EGI's power bus.
    assert cuts == {
        ("mission_computer",),
        ("power_bus_1", "power_bus_2"),
        ("bus_ch_a", "bus_ch_b"),
        ("egi_1", "egi_2"),
        ("egi_1", "power_bus_2"),
        ("egi_2", "power_bus_1"),
    }


# --- the navigation system -------------------------------------------------------------------


def test_parameters_carry_a_basis() -> None:
    rows = load_parameters()
    assert set(rows) == {
        "egi_1",
        "egi_2",
        "power_bus_1",
        "power_bus_2",
        "bus_ch_a",
        "bus_ch_b",
        "mission_computer",
    }
    assert all("CPS-01" in r.basis and "assumption" in r.basis for r in rows.values())


@pytest.mark.parametrize("hours", [1.0, MISSION_HOURS, 1000.0])
def test_navigation_matches_hand_derived_closed_form(hours: float) -> None:
    m = navigation_model()
    q = m.probabilities(hours)
    expected = navigation_unreliability(
        q["egi_1"], q["power_bus_1"], q["bus_ch_a"], q["mission_computer"]
    )
    assert unreliability(m, hours) == pytest.approx(expected, rel=1e-12)


def test_extra_units_copy_unit_one() -> None:
    specs = component_specs(egi_units=3, bus_channels=3)
    assert specs["egi_3"].failure_rate_per_hour == specs["egi_1"].failure_rate_per_hour
    assert specs["bus_ch_c"].failure_rate_per_hour == specs["bus_ch_a"].failure_rate_per_hour
    m = navigation_model(3, 3)
    assert len(m.components) == 9
    with pytest.raises(ValueError):
        navigation_model(0, 2)
    with pytest.raises(ValueError):
        navigation_model(mission_computers=5)
    dual = navigation_model(mission_computers=2)
    assert "mission_computer_2" in dual.components
    assert "2 mission computers" in dual.name


def test_more_egis_lower_unreliability_toward_the_floor() -> None:
    # Under independence, more EGIs only remove the EGI terms; the floor is the mission computer
    # plus the power and bus terms, which no EGI can remove.
    q = [unreliability(navigation_model(n, 2), MISSION_HOURS) for n in (1, 2, 3, 4)]
    assert q[0] > q[1] > q[2] > q[3]
    floor = navigation_unreliability(
        0.0, *[BasicEvent("x", r).probability(MISSION_HOURS) for r in (2e-5, 1e-5, 5e-5)]
    )
    assert q[3] > floor


def test_parameters_load_from_a_given_path(tmp_path: Path) -> None:
    from importlib import resources

    text = resources.files("cyberccf.data").joinpath("system_parameters.csv").read_text()
    path = tmp_path / "p.csv"
    path.write_text(text.replace("5.0e-5", "1.0e-4"))
    assert load_parameters(path)["mission_computer"].failure_rate_per_hour == 1e-4
    m = navigation_model(parameters=path)
    assert m.event("mission_computer").rate_per_hour == 1e-4


def test_affected_lists_the_components_an_event_fails() -> None:
    m = navigation_model()
    assert m.affected("power_bus_1") == ["power_bus_1"]


def test_the_failure_bdd_is_built_once_per_model() -> None:
    from cyberccf.independence_baseline.model import failure_bdd

    m = navigation_model()
    first = failure_bdd(m)
    assert failure_bdd(m) is first
    assert unreliability(m, 1.0) < unreliability(m, MISSION_HOURS)  # same BDD, other q
