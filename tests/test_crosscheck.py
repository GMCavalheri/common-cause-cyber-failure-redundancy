"""Cross-checks with CPS-01 and CPS-02: the same synthetic system, computed by other models.

CPS-02 (``cpsrbd`` v1.0.0) models the navigation system as a unified RBD + attack-tree DAG in
failure logic and computes P(loss of trusted navigation) exactly by Shannon decomposition;
with every cyber step switched off it is the classical reliability view. CPS-01 (``cyberrel``
v1.0.0) computes the same mission reliability by state enumeration in success logic. This
project's factoring engine must give the same number: three independent implementations.
"""

from __future__ import annotations

import pytest

from cyberccf.independence_baseline import MISSION_HOURS, navigation_model, unreliability

cpsrbd = pytest.importorskip("cpsrbd")
cyberrel = pytest.importorskip("cyberrel")

from cpsrbd.consequence_driven_analysis import navigation_case_study  # noqa: E402
from cpsrbd.probability_likelihood_propagation import (  # noqa: E402
    exact_probability,
    origin_overrides,
)
from cpsrbd.unified_graph_model import Origin  # noqa: E402
from cyberrel.system_model import mission_reliability, navigation_system  # noqa: E402

# CPS-02 basic event -> this project's component (same failure rates, see the CSVs).
CPS02_NAMES = {
    "egi_1_hw": "egi_1",
    "egi_2_hw": "egi_2",
    "power_bus_1": "power_bus_1",
    "power_bus_2": "power_bus_2",
    "bus_ch_a": "bus_ch_a",
    "bus_ch_b": "bus_ch_b",
    "mc_hw": "mission_computer",
}


def test_pinned_versions() -> None:
    assert cpsrbd.__version__ == "1.0.0"
    assert cyberrel.__version__ == "1.0.0"


def test_failure_rates_match_cps01_and_cps02() -> None:
    ours = navigation_model()
    for event in navigation_case_study().basic_events():
        if event.name in CPS02_NAMES:
            assert (
                ours.event(CPS02_NAMES[event.name]).rate_per_hour
                == (event.attributes["failure_rate"])
            )
    theirs = navigation_system()
    for comp in ours.components:
        assert ours.event(comp).rate_per_hour == theirs.component(comp).failure_rate


@pytest.mark.parametrize("hours", [1.0, MISSION_HOURS, 100.0])
def test_mission_unreliability_matches_cps02(hours: float) -> None:
    model = navigation_case_study(mission_hours=hours)
    expected = exact_probability(model, origin_overrides(model, Origin.PHYSICAL))
    assert unreliability(navigation_model(), hours) == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize(("egis", "buses"), [(1, 1), (2, 2), (3, 2), (2, 3), (4, 4)])
@pytest.mark.parametrize("hours", [MISSION_HOURS, 500.0])
def test_mission_unreliability_matches_cps01(egis: int, buses: int, hours: float) -> None:
    expected = 1.0 - mission_reliability(navigation_system(egis, buses), hours)
    assert unreliability(navigation_model(egis, buses), hours) == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("computers", [2, 3])
def test_redundant_mission_computers_match_cps01(computers: int) -> None:
    expected = 1.0 - mission_reliability(navigation_system(mission_computers=computers), 10.0)
    got = unreliability(navigation_model(mission_computers=computers), 10.0)
    assert got == pytest.approx(expected, rel=1e-12)
