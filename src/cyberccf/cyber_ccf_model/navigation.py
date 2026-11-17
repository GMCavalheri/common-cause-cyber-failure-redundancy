"""Cyber common cause on the navigation system: attributes of the programmable channels.

The EGIs and the mission computers are programmable, so they carry firmware or software,
network and supply-chain attributes (``data/navigation_attributes.csv``); cables and power
buses do not. The baseline fits identical units: every EGI has the same three values, and so
does every mission computer.

``distinct[(group, dimension)] = n`` gives that group ``n`` different values of that attribute
(member ``i`` gets value ``i mod n``), which is how diversity is expressed: ``n = 1`` is
identical channels, ``n = members`` fully diverse. ``shared_network = True`` puts the EGIs and
the mission computers on one segment, so a single network event reaches both groups.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping
from importlib import resources

from cyberccf.cyber_ccf_model.shared_vulnerability import (
    DIMENSIONS,
    Exposure,
    apply_cyber,
    load_exposures,
    scaled,
)
from cyberccf.independence_baseline.model import Model
from cyberccf.independence_baseline.navigation import component_specs
from cyberccf.physical_ccf_beta_factor.navigation import physical_ccf_model

PROGRAMMABLE = ("nav_source", "mission_computer")


def load_attribute_table() -> dict[str, dict[str, str]]:
    """Baseline attribute values per programmable component group."""
    text = resources.files("cyberccf.data").joinpath("navigation_attributes.csv").read_text()
    return {
        r["component_group"]: {d: r[d] for d in DIMENSIONS}
        for r in csv.DictReader(text.splitlines())
    }


def navigation_attributes(
    egi_units: int = 2,
    mission_computers: int = 1,
    distinct: Mapping[tuple[str, str], int] | None = None,
    shared_network: bool = False,
) -> dict[str, dict[str, str]]:
    """Attribute values of every programmable component."""
    base = load_attribute_table()
    distinct = distinct or {}
    specs = component_specs(egi_units, 2, mission_computers=mission_computers)
    members: dict[str, list[str]] = {g: [] for g in PROGRAMMABLE}
    for name, spec in specs.items():
        if spec.group in members:
            members[spec.group].append(name)
    out: dict[str, dict[str, str]] = {}
    for group, comps in members.items():
        for i, comp in enumerate(comps):
            attrs = {}
            for dim in DIMENSIONS:
                n = distinct.get((group, dim), 1)
                if not 1 <= n <= len(comps):
                    raise ValueError(f"{group}/{dim}: distinct values must be 1..{len(comps)}")
                value = base[group][dim]
                if dim == "network" and shared_network:
                    value = "shared_net"
                attrs[dim] = value if n == 1 else f"{value}_{i % n + 1}"
            out[comp] = attrs
    return out


def cyber_ccf_model(
    egi_units: int = 2,
    bus_channels: int = 2,
    mission_computers: int = 1,
    betas: Mapping[str, float] | None = None,
    distinct: Mapping[tuple[str, str], int] | None = None,
    shared_network: bool = False,
    exposure_scale: float = 1.0,
    exposures: Mapping[str, Exposure] | None = None,
) -> Model:
    """The navigation system with physical common cause and shared cyber vulnerabilities."""
    physical = physical_ccf_model(egi_units, bus_channels, mission_computers, betas)
    attrs = navigation_attributes(egi_units, mission_computers, distinct, shared_network)
    exp = scaled(exposures or load_exposures(), exposure_scale)
    return apply_cyber(physical, attrs, exp)
