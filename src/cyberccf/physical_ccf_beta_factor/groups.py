"""Adding a common-cause component group to a model, as shared basic events.

A group of ``m`` components with the same total failure rate ``lambda_t`` and fractions
``f_k`` (from :mod:`~cyberccf.physical_ccf_beta_factor.parametric`) becomes, in the basic-event
formulation of NUREG/CR-5485 (section 5.3, the "expanded fault tree"):

* each member's own event, now at rate ``f_1 lambda_t``;
* for each subset ``S`` of the members with ``|S| = k >= 2`` and ``f_k > 0``, a new event at
  rate ``f_k lambda_t`` that is a cause of every member of ``S``.

The exact engine of Phase 1 then quantifies the model with no approximation: the factoring
pivots on the new shared events.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from itertools import combinations

from cyberccf.independence_baseline.model import BasicEvent, Model
from cyberccf.physical_ccf_beta_factor.parametric import beta_factor_fractions, check_fractions


@dataclass(frozen=True)
class CCFGroup:
    """A common-cause component group and its fractions ``f_1..f_m``."""

    name: str
    members: tuple[str, ...]
    fractions: tuple[float, ...]
    kind: str = "physical_ccf"
    basis: str = ""

    def __post_init__(self) -> None:
        if len(set(self.members)) != len(self.members) or len(self.members) < 2:
            raise ValueError("a group needs at least two distinct members")
        check_fractions(len(self.members), self.fractions)


def beta_group(
    name: str, members: Sequence[str], beta: float, kind: str = "physical_ccf", basis: str = ""
) -> CCFGroup:
    """A beta-factor group over ``members``."""
    return CCFGroup(
        name, tuple(members), tuple(beta_factor_fractions(len(members), beta)), kind, basis
    )


def ccf_event_name(group: str, subset: Sequence[str]) -> str:
    """Name of the event that fails exactly ``subset`` of ``group``."""
    return f"{group}[{'+'.join(subset)}]"


def apply_ccf(model: Model, group: CCFGroup) -> Model:
    """The model with ``group``'s members' own failures split into independent and CCF parts.

    Each member must be failed by exactly one event of kind ``independent`` (its own), and all
    members must share the same total rate: the parametric models assume identical members.
    """
    own = {}
    for member in group.members:
        if member not in model.causes:
            raise ValueError(f"{member!r} is not a component of the model")
        mine = [e for e in model.causes[member] if model.event(e).kind == "independent"]
        if len(mine) != 1:
            raise ValueError(f"{member!r} must have exactly one independent event")
        own[member] = model.event(mine[0])
    rates = {e.rate_per_hour for e in own.values()}
    if len(rates) != 1:
        raise ValueError(f"group {group.name!r} members have different rates {sorted(rates)}")
    lam = rates.pop()

    f = group.fractions
    events = [
        replace(e, rate_per_hour=f[0] * lam) if e in own.values() else e for e in model.events
    ]
    causes = {c: list(v) for c, v in model.causes.items()}
    for k in range(2, len(group.members) + 1):
        if f[k - 1] == 0.0:
            continue
        for subset in combinations(group.members, k):
            name = ccf_event_name(group.name, subset)
            events.append(
                BasicEvent(
                    name,
                    f[k - 1] * lam,
                    group.kind,
                    f"{group.name}: common cause fails {', '.join(subset)}",
                    group.basis,
                )
            )
            for member in subset:
                causes[member].append(name)
    return Model(
        f"{model.name} + {group.name}",
        model.structure,
        tuple(events),
        {c: tuple(v) for c, v in causes.items()},
    )


def apply_groups(model: Model, groups: Sequence[CCFGroup]) -> Model:
    """Apply several (disjoint) groups in turn."""
    for g in groups:
        model = apply_ccf(model, g)
    return model
