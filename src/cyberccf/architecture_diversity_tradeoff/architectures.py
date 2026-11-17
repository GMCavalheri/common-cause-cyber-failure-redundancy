"""Candidate architectures of the navigation system, their cost and their unreliability.

An architecture fixes how many EGIs and mission computers are fitted and, for each
programmable group and each attribute, how many distinct values its members use (1 =
identical, the group size = fully diverse). The cost of an architecture is the sum of
illustrative relative costs (``data/diversity_costs.csv``) of what it adds to the baseline of
two identical EGIs and one mission computer.

Changing the cyber exposure changes only event rates, not the model's structure, so the
unreliability at any exposure scale is computed from one BDD per architecture
(:func:`unreliability_at_scale`).
"""

from __future__ import annotations

import csv
import math
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from importlib import resources
from itertools import product

from cyberccf.cyber_ccf_model.navigation import cyber_ccf_model
from cyberccf.cyber_ccf_model.shared_vulnerability import DIMENSIONS
from cyberccf.independence_baseline.model import Model, failure_probability

BASE_EGIS = 2
BASE_COMPUTERS = 1
ITEM_OF = {
    "firmware": "firmware_variant",
    "network": "network_variant",
    "supply_chain": "supplier_variant",
}


@dataclass(frozen=True)
class Architecture:
    """A design point: unit counts and the number of distinct attribute values per group."""

    egi_units: int = 2
    mission_computers: int = 1
    distinct: tuple[tuple[tuple[str, str], int], ...] = field(default_factory=tuple)

    def distinct_map(self) -> dict[tuple[str, str], int]:
        """``distinct`` as a dictionary."""
        return dict(self.distinct)

    @property
    def label(self) -> str:
        """Compact name, e.g. ``3 EGI [fw 2, net 3] + 2 MC [fw 2]``."""
        short = {"firmware": "fw", "network": "net", "supply_chain": "src"}
        d = self.distinct_map()

        def part(group: str, n_units: int, tag: str) -> str:
            div = [
                f"{short[dim]} {d[(group, dim)]}"
                for dim in DIMENSIONS
                if d.get((group, dim), 1) > 1
            ]
            return f"{n_units} {tag}" + (f" [{', '.join(div)}]" if div else "")

        egis = part("nav_source", self.egi_units, "EGI")
        return f"{egis} + {part('mission_computer', self.mission_computers, 'MC')}"

    def model(self) -> Model:
        """The navigation model of this architecture at the illustrative cyber exposure."""
        return cyber_ccf_model(
            egi_units=self.egi_units,
            mission_computers=self.mission_computers,
            distinct=self.distinct_map(),
        )


def make_architecture(
    egi_units: int, mission_computers: int, distinct: Mapping[tuple[str, str], int] | None = None
) -> Architecture:
    """An architecture with ``distinct`` normalised (entries of 1 dropped, sorted)."""
    items = tuple(sorted((k, v) for k, v in (distinct or {}).items() if v > 1))
    return Architecture(egi_units, mission_computers, items)


def enumerate_architectures(
    egi_options: tuple[int, ...] = (2, 3), computer_options: tuple[int, ...] = (1, 2)
) -> Iterator[Architecture]:
    """Every combination of unit counts and per-attribute diversity levels."""
    for n_egi, n_mc in product(egi_options, computer_options):
        egi_levels = [range(1, n_egi + 1)] * len(DIMENSIONS)
        mc_levels = [range(1, n_mc + 1)] * len(DIMENSIONS)
        for egi_d in product(*egi_levels):
            for mc_d in product(*mc_levels):
                distinct = {("nav_source", d): v for d, v in zip(DIMENSIONS, egi_d, strict=True)}
                distinct |= {
                    ("mission_computer", d): v for d, v in zip(DIMENSIONS, mc_d, strict=True)
                }
                yield make_architecture(n_egi, n_mc, distinct)


@dataclass(frozen=True)
class CostItem:
    """One row of the cost table."""

    item: str
    component_group: str
    cost: float
    basis: str


def load_costs() -> dict[tuple[str, str], CostItem]:
    """Relative costs keyed by (item, component group)."""
    text = resources.files("cyberccf.data").joinpath("diversity_costs.csv").read_text()
    rows = [
        CostItem(r["item"], r["component_group"], float(r["cost"]), r["basis"])
        for r in csv.DictReader(text.splitlines())
    ]
    return {(r.item, r.component_group): r for r in rows}


def cost(arch: Architecture, costs: Mapping[tuple[str, str], CostItem] | None = None) -> float:
    """Relative cost of what the architecture adds to two identical EGIs and one computer."""
    c = costs or load_costs()
    total = (arch.egi_units - BASE_EGIS) * c[("extra_unit", "nav_source")].cost
    total += (arch.mission_computers - BASE_COMPUTERS) * c[("extra_unit", "mission_computer")].cost
    for (group, dim), n in arch.distinct:
        total += (n - 1) * c[(ITEM_OF[dim], group)].cost
    return total


def unreliability_at_scale(model: Model, hours: float, cyber_scale: float) -> float:
    """Mission unreliability with every cyber event's rate multiplied by ``cyber_scale``.

    Same as building the model with ``exposure_scale = cyber_scale`` (tested), but reuses the
    model's BDD.
    """
    if cyber_scale < 0:
        raise ValueError("cyber_scale must be >= 0")
    q = {}
    for e in model.events:
        rate = e.rate_per_hour * (cyber_scale if e.kind.startswith("cyber") else 1.0)
        q[e.name] = -math.expm1(-rate * hours)
    return failure_probability(model, q)
