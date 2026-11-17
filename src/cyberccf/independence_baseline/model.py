"""Basic events, components and exact quantification of a reliability model.

The model is the standard *basic-event* formulation of fault-tree and CCF analysis
(NUREG/CR-5485, section 2): a **component** fails when any of the basic events that cause it
occurs, and basic events are mutually independent. With one event per component this is the
classical independence model. A common-cause event is simply a basic event listed as a cause
of several components, so physical and cyber common cause (Phases 2-3) reuse this engine
unchanged.

Basic events occur at a constant rate ``lambda`` (per hour); over a mission of ``t`` hours an
event occurs with probability ``q = 1 - exp(-lambda t)``.

**Exact quantification by factoring.** If every basic event influences at most one leaf
occurrence of the block diagram, the children of each block are independent and the success
probability is computed bottom-up. Otherwise each *shared* event ``e`` is conditioned on
(Shannon decomposition, the pivotal decomposition of Barlow & Proschan, *Statistical Theory
of Reliability and Life Testing*, 1975, ch. 2)::

    P(fail) = q_e P(fail | e occurs) + (1 - q_e) P(fail | e does not occur)

until no shared event is left. The cost is ``2**s`` bottom-up evaluations for ``s`` shared
events, which stays small for the architectures studied here.
:func:`enumerate_failure_probability` is the brute-force oracle used by the tests: it
enumerates all ``2**m`` states of the ``m`` basic events.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import combinations, product

from cyberccf.independence_baseline.structure import Block, at_least_k, components_in, leaves

KINDS = ("independent", "physical_ccf", "cyber_ccf")
"""The origin of a basic event: one component's own failure, a shared physical cause, or a
shared cyber vulnerability."""


@dataclass(frozen=True)
class BasicEvent:
    """An event that occurs at a constant rate and fails every component it is a cause of."""

    name: str
    rate_per_hour: float
    kind: str = "independent"
    description: str = ""
    basis: str = ""

    def __post_init__(self) -> None:
        if not self.rate_per_hour >= 0 or math.isinf(self.rate_per_hour):
            raise ValueError(f"{self.name}: rate must be finite and >= 0")
        if self.kind not in KINDS:
            raise ValueError(f"{self.name}: kind must be one of {KINDS}, got {self.kind!r}")

    def probability(self, hours: float) -> float:
        """``P(the event occurs within hours)`` = ``1 - exp(-lambda t)``."""
        if hours < 0:
            raise ValueError(f"mission length must be >= 0, got {hours}")
        return -math.expm1(-self.rate_per_hour * hours)


@dataclass(frozen=True)
class Model:
    """A block diagram plus, for each component, the basic events that fail it."""

    name: str
    structure: Block
    events: tuple[BasicEvent, ...]
    causes: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        names = [e.name for e in self.events]
        if len(set(names)) != len(names):
            raise ValueError("basic event names must be unique")
        known = set(names)
        for comp in self.components:
            if comp not in self.causes or not self.causes[comp]:
                raise ValueError(f"component {comp!r} has no basic event")
            missing = set(self.causes[comp]) - known
            if missing:
                raise ValueError(f"component {comp!r} refers to unknown events {sorted(missing)}")
        extra = set(self.causes) - set(self.components)
        if extra:
            raise ValueError(f"causes given for components not in the structure: {extra}")

    @property
    def components(self) -> list[str]:
        """Distinct components in the structure, in first-seen order."""
        return components_in(self.structure)

    def event(self, name: str) -> BasicEvent:
        """The basic event with this name."""
        for e in self.events:
            if e.name == name:
                return e
        raise KeyError(name)

    def probabilities(self, hours: float) -> dict[str, float]:
        """Mission probability of every basic event."""
        return {e.name: e.probability(hours) for e in self.events}

    def affected(self, event: str) -> list[str]:
        """The components this event fails."""
        return [c for c in self.components if event in self.causes[c]]


def independent_model(
    name: str,
    structure: Block,
    rates: Mapping[str, float],
    descriptions: Mapping[str, str] | None = None,
    bases: Mapping[str, str] | None = None,
) -> Model:
    """The classical model: each component fails only through its own basic event."""
    comps = components_in(structure)
    descriptions = descriptions or {}
    bases = bases or {}
    events = tuple(
        BasicEvent(c, rates[c], "independent", descriptions.get(c, ""), bases.get(c, ""))
        for c in comps
    )
    return Model(name, structure, events, {c: (c,) for c in comps})


def _success(block: Block, leaf_fail: Mapping[str, float]) -> float:
    if isinstance(block, str):
        return 1.0 - leaf_fail[block]
    return at_least_k(block.k, [_success(c, leaf_fail) for c in block.children])


def _leaf_fail(model: Model, q: Mapping[str, float]) -> dict[str, float]:
    out = {}
    for comp in model.components:
        survive = 1.0
        for e in model.causes[comp]:
            survive *= 1.0 - q[e]
        out[comp] = 1.0 - survive
    return out


def shared_events(model: Model) -> list[str]:
    """Events that influence more than one leaf occurrence (the ones factoring must pivot on)."""
    counts: Counter[str] = Counter()
    for leaf in leaves(model.structure):
        counts.update(model.causes[leaf])
    return [e.name for e in model.events if counts[e.name] > 1]


def failure_probability(model: Model, q: Mapping[str, float]) -> float:
    """Exact ``P(system fails)`` given the occurrence probability ``q`` of every basic event."""
    for name, p in q.items():
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"{name}: probability {p} outside [0, 1]")
    pivots = [e for e in shared_events(model) if 0.0 < q[e] < 1.0]

    def rec(i: int, cond: dict[str, float]) -> float:
        if i == len(pivots):
            return 1.0 - _success(model.structure, _leaf_fail(model, cond))
        e, p = pivots[i], cond[pivots[i]]
        return p * rec(i + 1, {**cond, e: 1.0}) + (1.0 - p) * rec(i + 1, {**cond, e: 0.0})

    return rec(0, dict(q))


def unreliability(model: Model, hours: float) -> float:
    """``P(system fails within a mission of hours)`` with no repair during the mission."""
    return failure_probability(model, model.probabilities(hours))


def system_works(model: Model, occurred: Mapping[str, bool]) -> bool:
    """The structure function: does the system work when exactly these events occurred?"""
    leaf_fail = {c: float(any(occurred[e] for e in model.causes[c])) for c in model.components}
    return _success(model.structure, leaf_fail) == 1.0


def enumerate_failure_probability(model: Model, q: Mapping[str, float]) -> float:
    """Brute-force oracle: sum the probability of every event state in which the system fails."""
    names = [e.name for e in model.events]
    if len(names) > 22:
        raise ValueError("too many basic events to enumerate")
    total = 0.0
    for state in product((False, True), repeat=len(names)):
        occurred = dict(zip(names, state, strict=True))
        if system_works(model, occurred):
            continue
        w = 1.0
        for name, s in occurred.items():
            w *= q[name] if s else 1.0 - q[name]
        total += w
    return total


def minimal_cut_sets(model: Model, max_order: int = 4) -> list[frozenset[str]]:
    """Minimal sets of basic events whose joint occurrence fails the system (up to max_order).

    Found by checking event subsets in order of size and keeping those that fail the system
    and contain no smaller cut set. Used to explain *why* common cause dominates: a CCF event
    is a cut set of order one.
    """
    names = [e.name for e in model.events]
    cuts: list[frozenset[str]] = []
    for order in range(1, max_order + 1):
        for subset in combinations(names, order):
            s = frozenset(subset)
            if any(c <= s for c in cuts):
                continue
            if not system_works(model, {n: n in s for n in names}):
                cuts.append(s)
    return cuts
