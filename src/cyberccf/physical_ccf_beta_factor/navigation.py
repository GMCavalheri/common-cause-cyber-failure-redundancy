"""Physical common cause on the navigation system: one beta-factor group per redundant set.

Every redundant set of identical components becomes a common-cause group: the EGIs, the data
bus channels, the power buses and, when two or more are fitted, the mission computers. The
beta values are in ``data/ccf_parameters.csv``; every one is an assumption inside the range
IEC 61508-6 Annex D gives for its kind of equipment, as quoted by a free secondary source.
"""

from __future__ import annotations

import csv
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources

from cyberccf.independence_baseline.model import Model
from cyberccf.independence_baseline.navigation import component_specs, navigation_model
from cyberccf.physical_ccf_beta_factor.groups import CCFGroup, apply_groups, beta_group


@dataclass(frozen=True)
class BetaRow:
    """One row of ``ccf_parameters.csv``."""

    group: str
    component_group: str
    beta: float
    basis: str


def load_ccf_parameters() -> dict[str, BetaRow]:
    """The physical beta factors, keyed by the component group they apply to."""
    text = resources.files("cyberccf.data").joinpath("ccf_parameters.csv").read_text()
    rows = [
        BetaRow(r["group"], r["component_group"], float(r["beta"]), r["basis"])
        for r in csv.DictReader(text.splitlines())
    ]
    return {r.component_group: r for r in rows}


def physical_groups(
    model: Model,
    betas: Mapping[str, float] | None = None,
    egi_units: int = 2,
    bus_channels: int = 2,
    mission_computers: int = 1,
) -> list[CCFGroup]:
    """One beta-factor group per redundant set of the navigation model.

    ``betas`` overrides the table by component group (``nav_source``, ``data_bus``, ``power``,
    ``mission_computer``); a beta of 0 leaves that set independent.
    """
    rows = load_ccf_parameters()
    beta = {g: r.beta for g, r in rows.items()} | dict(betas or {})
    specs = component_specs(egi_units, bus_channels, mission_computers=mission_computers)
    by_group: dict[str, list[str]] = {}
    for comp in model.components:
        by_group.setdefault(specs[comp].group, []).append(comp)
    groups = []
    for component_group, members in by_group.items():
        if len(members) < 2 or beta.get(component_group, 0.0) == 0.0:
            continue
        row = rows[component_group]
        groups.append(
            beta_group(row.group, members, beta[component_group], "physical_ccf", row.basis)
        )
    return groups


def physical_ccf_model(
    egi_units: int = 2,
    bus_channels: int = 2,
    mission_computers: int = 1,
    betas: Mapping[str, float] | None = None,
) -> Model:
    """The navigation system with physical common cause on every redundant set."""
    base = navigation_model(egi_units, bus_channels, mission_computers=mission_computers)
    groups = physical_groups(base, betas, egi_units, bus_channels, mission_computers)
    return apply_groups(base, groups)
