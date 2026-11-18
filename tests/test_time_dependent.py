"""Extra: Markov availability and Monte Carlo, against closed forms, CPS-01 and each other."""

from __future__ import annotations

import numpy as np
import pytest

from cyberccf.cyber_ccf_model import cyber_ccf_model
from cyberccf.independence_baseline import (
    MISSION_HOURS,
    Parallel,
    Series,
    component_specs,
    independent_model,
    navigation_model,
    unreliability,
)
from cyberccf.physical_ccf_beta_factor import apply_ccf, beta_group, physical_ccf_model
from cyberccf.time_dependent import (
    build_chain,
    one_of_two_markov,
    simulate_availability,
    simulate_missions,
    stationary,
    steady_state,
    transient_unreliability,
    wilson,
)


def mttr_of(n_egi: int = 2, n_mc: int = 1) -> dict[str, float]:
    return {n: s.mttr_hours for n, s in component_specs(n_egi, 2, mission_computers=n_mc).items()}


def pair(rate: float, beta: float) -> object:
    m = independent_model("p", Parallel("a", "b"), {"a": rate, "b": rate})
    return apply_ccf(m, beta_group("g", ["a", "b"], beta)) if beta > 0 else m


@pytest.mark.parametrize("beta", [0.0, 0.05, 0.5])
@pytest.mark.parametrize("mttr", [3.0, 50.0])
def test_one_of_two_closed_form(beta: float, mttr: float) -> None:
    rate = 1e-3
    ss = steady_state(pair(rate, beta), {"a": mttr, "b": mttr})  # type: ignore[arg-type]
    u, omega = one_of_two_markov((1 - beta) * rate, beta * rate, mttr)
    assert ss.unavailability == pytest.approx(u, rel=1e-9)
    assert ss.failure_frequency == pytest.approx(omega, rel=1e-9)
    if beta == 0:  # two independent units: binomial
        assert u == pytest.approx((rate / (rate + 1 / mttr)) ** 2, rel=1e-12)


def test_ccf_raises_unavailability_of_a_pair() -> None:
    u0, _ = one_of_two_markov(1e-3, 0.0, 5.0)
    u1, _ = one_of_two_markov(0.95e-3, 0.05e-3, 5.0)
    assert u1 > 5 * u0


@pytest.mark.parametrize("n_mc", [1, 2])
def test_independence_matches_cps01_steady_state(n_mc: int) -> None:
    # CPS-01 computes availability and MTBF of independent components exactly (enumeration and
    # Birnbaum importance); its lognormal repairs do not change steady-state results for
    # independent components, which depend only on the mean repair time.
    cyberrel = pytest.importorskip("cyberrel")
    from cyberrel.system_model import navigation_system
    from cyberrel.system_model.closed_form import steady_state as cps01_steady_state

    assert cyberrel.__version__ == "1.0.0"
    ours = steady_state(navigation_model(mission_computers=n_mc), mttr_of(n_mc=n_mc))
    theirs = cps01_steady_state(navigation_system(mission_computers=n_mc))
    assert ours.availability == pytest.approx(theirs.availability, rel=1e-12)
    assert ours.mtbf == pytest.approx(theirs.mtbf, rel=1e-9)
    assert ours.mdt == pytest.approx(theirs.mdt, rel=1e-9)


@pytest.mark.parametrize("hours", [MISSION_HOURS, 500.0])
@pytest.mark.parametrize("n_mc", [1, 2])
def test_markov_transient_equals_the_bdd(hours: float, n_mc: int) -> None:
    for model in (
        navigation_model(mission_computers=n_mc),
        physical_ccf_model(mission_computers=n_mc),
        cyber_ccf_model(mission_computers=n_mc),
        cyber_ccf_model(mission_computers=n_mc, shared_network=True),
    ):
        assert transient_unreliability(model, hours) == pytest.approx(
            unreliability(model, hours), rel=1e-9
        )


def test_stationary_is_a_distribution_and_metrics_are_consistent() -> None:
    model = cyber_ccf_model(mission_computers=2)
    chain = build_chain(model, mttr_of(n_mc=2))
    pi = stationary(chain.generator)
    assert pi.sum() == pytest.approx(1.0)
    assert np.allclose(pi @ chain.generator, 0.0, atol=1e-15)
    ss = steady_state(model, mttr_of(n_mc=2))
    assert ss.availability + ss.unavailability == pytest.approx(1.0, abs=1e-14)
    assert ss.mtbf / ss.mdt == pytest.approx(ss.availability / ss.unavailability, rel=1e-9)


def test_chain_validation() -> None:
    model = navigation_model()
    with pytest.raises(ValueError):
        build_chain(model, dict.fromkeys(model.components, 0.0))
    many = [f"c{i}" for i in range(13)]
    with pytest.raises(ValueError, match="too large"):
        build_chain(independent_model("m", Parallel(*many), dict.fromkeys(many, 1.0)), None)
    never = independent_model("n", Series("a"), {"a": 0.0})
    ss = steady_state(never, {"a": 1.0})
    assert ss.availability == 1.0 and ss.failure_frequency == 0.0


def test_wilson_interval() -> None:
    est = wilson(50, 100)
    assert est.low < 0.5 < est.high
    assert wilson(0, 100).low == 0.0
    assert est.covers(0.5) and not est.covers(0.9)


@pytest.mark.parametrize("shared_network", [False, True])
def test_simulated_missions_cover_the_exact_value(shared_network: bool) -> None:
    # Long missions make the probability large enough to estimate in a fast test.
    model = cyber_ccf_model(mission_computers=2, shared_network=shared_network)
    est = simulate_missions(model, 2000.0, 200_000, np.random.default_rng(1))
    assert est.covers(unreliability(model, 2000.0))


def test_simulated_availability_covers_the_markov_chain() -> None:
    # A 1-of-2 group with physical and cyber common cause in series with a third unit, with
    # rates high enough for a fast run. The interval is 99.7 % (Student-t over replications).
    from cyberccf.cyber_ccf_model import Exposure, apply_cyber

    base = independent_model(
        "s", Series(Parallel("a", "b"), "c"), {"a": 2e-2, "b": 2e-2, "c": 2e-3}
    )
    model = apply_cyber(
        apply_ccf(base, beta_group("g", ["a", "b"], 0.1)),
        {"a": {"firmware": "X"}, "b": {"firmware": "X"}},
        {"firmware": Exposure("firmware", 5e-3, 1.0)},
    )
    mttr = {"a": 5.0, "b": 5.0, "c": 8.0}
    exact = steady_state(model, mttr)
    sim = simulate_availability(model, mttr, 20_000.0, 30, np.random.default_rng(7))
    assert sim.unavailability.covers(exact.unavailability)
    assert sim.failure_frequency.covers(exact.failure_frequency)
    with pytest.raises(ValueError):
        simulate_availability(model, mttr, 10.0, 1, np.random.default_rng(0))
