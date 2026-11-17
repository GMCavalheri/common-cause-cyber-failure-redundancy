"""Phase 5: redundancy as claimed vs as it is, on the navigation system of the CPS series.

Three views of the same design:

* **as claimed**: independent channels (Lesson 1);
* **physical CCF**: the classical correction (Lesson 2);
* **physical + cyber CCF**: this project's correction (Lesson 3), shown at the illustrative
  exposure and across the range ``EXPOSURE_RANGE``, because the cyber rates have no
  field-data basis.

Plus a tornado analysis of every parameter and a robust recommendation: since unreliability
never decreases with the exposure (tested), the worst case over the range is its top end, so
the recommended design is the cheapest one that meets the requirement there.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from cyberccf.architecture_diversity_tradeoff.architectures import (
    Architecture,
    cost,
    enumerate_architectures,
    make_architecture,
    unreliability_at_scale,
)
from cyberccf.cyber_ccf_model.navigation import cyber_ccf_model
from cyberccf.cyber_ccf_model.shared_vulnerability import DIMENSIONS
from cyberccf.independence_baseline.model import (
    BasicEvent,
    Model,
    failure_probability,
    unreliability,
)
from cyberccf.independence_baseline.navigation import MISSION_HOURS, navigation_model
from cyberccf.physical_ccf_beta_factor.navigation import physical_ccf_model

EXPOSURE_RANGE = (0.25, 10.0)
"""Cyber exposure explored around the illustrative rates (multiplier)."""
REQUIREMENT = 1e-4
"""Illustrative requirement: P(loss of trusted navigation) per 10-hour mission (assumption)."""

SINGLE_STRING = make_architecture(1, 1)
"""One EGI and one computer (bus channels reduced to one as well, see ``views``)."""
REDUNDANT = make_architecture(2, 2)
"""Two identical EGIs, two bus channels, two identical mission computers: redundancy as usually
designed."""


@dataclass(frozen=True)
class Views:
    """P(loss of navigation) of one design under the three models."""

    label: str
    as_claimed: float
    physical: float
    cyber: float
    cyber_low: float
    cyber_high: float


def views(arch: Architecture, bus_channels: int = 2, hours: float = MISSION_HOURS) -> Views:
    """The design under independence, physical CCF and physical + cyber CCF."""
    ind = navigation_model(arch.egi_units, bus_channels, mission_computers=arch.mission_computers)
    phys = physical_ccf_model(arch.egi_units, bus_channels, arch.mission_computers)
    cyb = cyber_ccf_model(
        arch.egi_units, bus_channels, arch.mission_computers, distinct=arch.distinct_map()
    )
    lo, hi = EXPOSURE_RANGE
    return Views(
        arch.label if bus_channels == 2 else f"{arch.label}, {bus_channels} bus channel",
        unreliability(ind, hours),
        unreliability(phys, hours),
        unreliability(cyb, hours),
        unreliability_at_scale(cyb, hours, lo),
        unreliability_at_scale(cyb, hours, hi),
    )


def unreliability_with(model: Model, hours: float, factor: Callable[[BasicEvent], float]) -> float:
    """Mission unreliability with each event's rate multiplied by ``factor(event)``."""
    q = {}
    for e in model.events:
        f = factor(e)
        if f < 0:
            raise ValueError(f"negative factor for {e.name}")
        q[e.name] = -math.expm1(-e.rate_per_hour * f * hours)
    return failure_probability(model, q)


@dataclass(frozen=True)
class TornadoBar:
    """The swing of P(loss) when one parameter moves from its low to its high value."""

    parameter: str
    low_label: str
    high_label: str
    q_low: float
    q_high: float

    @property
    def swing(self) -> float:
        """``|q_high - q_low|``."""
        return abs(self.q_high - self.q_low)


def _physical_rate_factor(prefixes: tuple[str, ...], f: float) -> Callable[[BasicEvent], float]:
    def factor(e: BasicEvent) -> float:
        if e.kind.startswith("cyber"):
            return 1.0
        return f if e.name.startswith(prefixes) else 1.0

    return factor


def _cyber_factor(dimension: str, f: float) -> Callable[[BasicEvent], float]:
    def factor(e: BasicEvent) -> float:
        return f if e.name.startswith(f"cyber:{dimension}=") else 1.0

    return factor


def tornado(arch: Architecture = REDUNDANT, hours: float = MISSION_HOURS) -> list[TornadoBar]:
    """One bar per parameter, sorted by swing (largest first).

    Physical rates move from 0.5x to 2x; each beta factor across the IEC 61508-6 range quoted
    for its kind of equipment; each cyber exposure from 0x to 10x the illustrative value.
    """
    model = cyber_ccf_model(arch.egi_units, 2, arch.mission_computers, distinct=arch.distinct_map())
    bars = []
    groups = {
        "EGI physical rate": ("egi_",),
        "mission computer physical rate": ("mission_computer", "mc_ccf"),
        "bus channel physical rate": ("bus_",),
        "power bus physical rate": ("power_",),
    }
    for name, prefixes in groups.items():
        lo = unreliability_with(model, hours, _physical_rate_factor(prefixes, 0.5))
        hi = unreliability_with(model, hours, _physical_rate_factor(prefixes, 2.0))
        bars.append(TornadoBar(name, "× 0.5", "× 2", lo, hi))
    beta_ranges = {
        "nav_source": (0.005, 0.05),
        "mission_computer": (0.005, 0.05),
        "data_bus": (0.01, 0.1),
        "power": (0.01, 0.1),
    }
    for group, (lo_b, hi_b) in beta_ranges.items():
        q = []
        for b in (lo_b, hi_b):
            m = cyber_ccf_model(
                arch.egi_units, 2, arch.mission_computers, {group: b}, arch.distinct_map()
            )
            q.append(unreliability(m, hours))
        bars.append(TornadoBar(f"β of {group}", f"{lo_b:g}", f"{hi_b:g}", q[0], q[1]))
    for dim in DIMENSIONS:
        lo = unreliability_with(model, hours, _cyber_factor(dim, 0.0))
        hi = unreliability_with(model, hours, _cyber_factor(dim, 10.0))
        bars.append(TornadoBar(f"{dim} exposure", "× 0", "× 10", lo, hi))
    return sorted(bars, key=lambda b: -b.swing)


@dataclass(frozen=True)
class Recommendation:
    """The cheapest design meeting the requirement at the top of the exposure range."""

    architecture: Architecture
    cost: float
    q_illustrative: float
    q_worst: float


def recommend(
    requirement: float = REQUIREMENT,
    hours: float = MISSION_HOURS,
    candidates: list[Architecture] | None = None,
) -> Recommendation | None:
    """Cheapest design whose unreliability at the top of ``EXPOSURE_RANGE`` meets ``requirement``.

    Ties in cost go to the lower worst case. ``None`` if no candidate meets it.
    """
    hi = EXPOSURE_RANGE[1]
    best: Recommendation | None = None
    for arch in candidates or list(enumerate_architectures()):
        model = arch.model()
        worst = unreliability_at_scale(model, hours, hi)
        if worst > requirement:
            continue
        c = cost(arch)
        if best is None or (c, worst) < (best.cost, best.q_worst):
            best = Recommendation(arch, c, unreliability(model, hours), worst)
    return best
