"""The case-study system of the CPS series: navigation data delivered to a mission computer.

This is the architecture of CPS-02 (``cpsrbd``) and CPS-01 (``cyberrel``), so the series
analyses one system. A generic, defense-representative platform (no real system is modelled)
carries two embedded GNSS/INS navigation units (EGI), each powered from its own electrical
bus, that publish navigation solutions on a dual-channel data bus to a mission computer fed
from both power buses. The function is **"trusted navigation data reaches the mission
computer"**. In success logic::

    series(
        parallel(series(egi_1, power_bus_1), series(egi_2, power_bus_2)),  # a source
        parallel(bus_ch_a, bus_ch_b),                                      # a data path
        mission_computer,                                                  # the consumer
        parallel(power_bus_1, power_bus_2),                                # its power
    )

Every value in ``data/system_parameters.csv`` is copied from CPS-01 with its basis; all of
them are assumptions, not data from any real platform. ``egi_units`` and ``bus_channels``
change the redundancy: extra units copy unit 1's parameters, and EGI ``i`` is powered from
bus ``1 + (i - 1) % 2``, as in CPS-01. With ``mission_computers > 1`` the computers
(``mission_computer_1``, ...) work in parallel, each fed from both power buses, and copy the
single computer's parameters, also as in CPS-01. That variant matters here: the single
computer is a series element that no common-cause model can make worse, while two identical
computers running the same software load are the textbook case of cyber common cause.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from cyberccf.independence_baseline.model import Model, independent_model
from cyberccf.independence_baseline.structure import Block, Parallel, Series

FUNCTION = "Trusted navigation data reaches the mission computer"
MISSION_HOURS = 10.0
"""One mission, as in CPS-01/02 (assumption)."""
CHANNEL_LETTERS = "abcdefgh"


@dataclass(frozen=True)
class ComponentSpec:
    """One row of the parameter table."""

    name: str
    group: str
    description: str
    failure_rate_per_hour: float
    mttr_hours: float
    basis: str


def load_parameters(path: Path | None = None) -> dict[str, ComponentSpec]:
    """Read the system parameter table, keyed by component name."""
    if path is None:
        text = resources.files("cyberccf.data").joinpath("system_parameters.csv").read_text()
    else:
        text = path.read_text()
    return {
        r["name"]: ComponentSpec(
            r["name"],
            r["group"],
            r["description"],
            float(r["failure_rate_per_hour"]),
            float(r["mttr_hours"]),
            r["basis"],
        )
        for r in csv.DictReader(text.splitlines())
    }


def egi_names(n: int) -> list[str]:
    """``egi_1`` ... ``egi_n``."""
    return [f"egi_{i}" for i in range(1, n + 1)]


def bus_names(m: int) -> list[str]:
    """``bus_ch_a`` ... for ``m`` channels."""
    return [f"bus_ch_{CHANNEL_LETTERS[j]}" for j in range(m)]


def computer_names(k: int) -> list[str]:
    """``mission_computer`` for one computer, else ``mission_computer_1`` ... ``_k``."""
    return ["mission_computer"] if k == 1 else [f"mission_computer_{i}" for i in range(1, k + 1)]


def navigation_structure(
    egi_units: int = 2, bus_channels: int = 2, mission_computers: int = 1
) -> Block:
    """The success-logic block diagram for the given redundancy."""
    if not 1 <= egi_units <= 8 or not 1 <= bus_channels <= len(CHANNEL_LETTERS):
        raise ValueError("egi_units and bus_channels must be between 1 and 8")
    if not 1 <= mission_computers <= 4:
        raise ValueError("mission_computers must be between 1 and 4")
    sources = [Series(e, f"power_bus_{1 + i % 2}") for i, e in enumerate(egi_names(egi_units))]
    return Series(
        Parallel(*sources),
        Parallel(*bus_names(bus_channels)),
        Parallel(*computer_names(mission_computers)),
        Parallel("power_bus_1", "power_bus_2"),
    )


def component_specs(
    egi_units: int = 2,
    bus_channels: int = 2,
    parameters: Path | None = None,
    mission_computers: int = 1,
) -> dict[str, ComponentSpec]:
    """Parameters of every component, extra units copying unit 1 / channel A."""
    rows = load_parameters(parameters)
    specs = {}
    for i, name in enumerate(egi_names(egi_units)):
        base = rows[name] if name in rows else rows["egi_1"]
        specs[name] = ComponentSpec(
            name,
            base.group,
            f"Embedded GNSS/INS navigation unit {i + 1}",
            base.failure_rate_per_hour,
            base.mttr_hours,
            base.basis,
        )
    for name in bus_names(bus_channels):
        base = rows[name] if name in rows else rows["bus_ch_a"]
        specs[name] = ComponentSpec(
            name,
            base.group,
            f"Data bus channel {name[-1].upper()} (cable and transceivers)",
            base.failure_rate_per_hour,
            base.mttr_hours,
            base.basis,
        )
    for name in ("power_bus_1", "power_bus_2"):
        specs[name] = rows[name]
    mc = rows["mission_computer"]
    for i, name in enumerate(computer_names(mission_computers)):
        description = mc.description if mission_computers == 1 else f"{mc.description} ({i + 1})"
        specs[name] = ComponentSpec(
            name, mc.group, description, mc.failure_rate_per_hour, mc.mttr_hours, mc.basis
        )
    return specs


def navigation_model(
    egi_units: int = 2,
    bus_channels: int = 2,
    parameters: Path | None = None,
    mission_computers: int = 1,
) -> Model:
    """The navigation system under the classical independence assumption."""
    specs = component_specs(egi_units, bus_channels, parameters, mission_computers)
    name = f"navigation ({egi_units} EGI, {bus_channels} bus channels"
    name += f", {mission_computers} mission computers)" if mission_computers > 1 else ")"
    return independent_model(
        name,
        navigation_structure(egi_units, bus_channels, mission_computers),
        {n: s.failure_rate_per_hour for n, s in specs.items()},
        {n: s.description for n, s in specs.items()},
        {n: s.basis for n, s in specs.items()},
    )
