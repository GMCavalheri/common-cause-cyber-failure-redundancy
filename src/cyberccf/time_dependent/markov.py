"""Availability and MTBF with repair, exactly, by a Markov chain over component states.

The mission results of Phases 1-5 assume no repair. Over the life of a fleet, components are
repaired and what matters is **availability** and **MTBF**, the units CPS-01 reported. Common
cause changes those too, and the effect is not obvious: a common-cause event takes several
channels down at once, but they come back on their own repair clocks.

**Model.** The state is the set of failed components (``2**n`` states). Every basic event of
the model keeps its Poisson rate and, when it occurs, fails every *working* component it covers
(an event that finds all of them already failed changes nothing). Every failed component is
repaired independently at rate ``mu_j = 1 / MTTR_j`` (exponential repair, each component with
its own repair resource, as in CPS-01). After a common-cause event each affected component is
repaired on its own clock; that is an assumption, since a cyber event might instead need one
coordinated recovery. The chain is a continuous-time Markov chain with generator ``G``, and:

* steady state: ``pi G = 0``, ``sum pi = 1``; availability ``A = sum_{x up} pi_x``;
* failure frequency: ``omega = sum_{x up} pi_x sum_{y down} G[x, y]`` (rate of up -> down);
* MTBF (mean up time) ``A / omega`` and MDT ``(1 - A) / omega``, as in CPS-01;
* with no repair, the probability of being down at ``t`` is ``(e^{Gt})[none failed, down]``,
  which must equal the BDD mission unreliability: two independent methods, one number.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import expm

from cyberccf.independence_baseline.model import Model, works_with_failed

MAX_COMPONENTS = 12


@dataclass(frozen=True)
class SteadyState:
    """Long-run metrics of the system function."""

    availability: float
    unavailability: float
    failure_frequency: float
    mtbf: float
    mdt: float


@dataclass(frozen=True)
class Chain:
    """The generator, the component order behind the state bits, and which states are up."""

    components: tuple[str, ...]
    generator: NDArray[np.float64]
    up: NDArray[np.bool_]


def build_chain(model: Model, mttr: Mapping[str, float] | None) -> Chain:
    """Generator over failed-component sets (bit ``j`` set = component ``j`` failed).

    ``mttr=None`` means no repair (for mission probabilities).
    """
    comps = tuple(model.components)
    n = len(comps)
    if n > MAX_COMPONENTS:
        raise ValueError(f"{n} components: the state space 2**n is too large")
    index = {c: j for j, c in enumerate(comps)}
    masks = []
    for e in model.events:
        mask = 0
        for c in model.affected(e.name):
            mask |= 1 << index[c]
        masks.append((mask, e.rate_per_hour))
    mu = [0.0] * n
    if mttr is not None:
        for j, c in enumerate(comps):
            if not mttr[c] > 0:
                raise ValueError(f"{c}: MTTR must be > 0")
            mu[j] = 1.0 / mttr[c]
    size = 1 << n
    g = np.zeros((size, size))
    up = np.zeros(size, dtype=bool)
    for x in range(size):
        up[x] = works_with_failed(model, {comps[j] for j in range(n) if x >> j & 1})
        for mask, rate in masks:
            y = x | mask
            if y != x and rate > 0:
                g[x, y] += rate
        for j in range(n):
            if x >> j & 1 and mu[j] > 0:
                g[x, x & ~(1 << j)] += mu[j]
    np.fill_diagonal(g, -g.sum(axis=1))
    return Chain(comps, g, up)


def stationary(g: NDArray[np.float64]) -> NDArray[np.float64]:
    """Solve ``pi G = 0`` with ``sum pi = 1`` (one balance equation replaced by normalisation)."""
    a = g.T.copy()
    a[-1, :] = 1.0
    b = np.zeros(g.shape[0])
    b[-1] = 1.0
    pi = np.clip(np.linalg.solve(a, b), 0.0, None)
    return np.asarray(pi / pi.sum(), dtype=np.float64)


def steady_state(model: Model, mttr: Mapping[str, float]) -> SteadyState:
    """Exact long-run availability, failure frequency, MTBF and MDT."""
    chain = build_chain(model, mttr)
    pi = stationary(chain.generator)
    a = float(pi[chain.up].sum())
    down = float(pi[~chain.up].sum())
    omega = float(pi[chain.up] @ chain.generator[np.ix_(chain.up, ~chain.up)].sum(axis=1))
    if omega == 0:
        return SteadyState(a, down, 0.0, math.inf, 0.0)
    return SteadyState(a, down, omega, a / omega, down / omega)


def transient_unreliability(model: Model, hours: float) -> float:
    """P(system down at ``hours``) with no repair, from ``e^{Gt}`` (an oracle for the BDD)."""
    chain = build_chain(model, None)
    p = expm(chain.generator * hours)[0]
    return float(p[~chain.up].sum())


def one_of_two_markov(
    rate_independent: float, rate_common: float, mttr: float
) -> tuple[float, float]:
    """Closed form for a 1-of-2 group with beta-factor CCF and independent repair.

    States 0, 1, 2 failed; ``a = 2 lambda_i``, ``b = lambda_cc``, ``c = lambda_i + lambda_cc``,
    ``mu = 1/MTTR``. Balance gives ``pi_1 = pi_0 (a + b)/mu`` and
    ``pi_2 = pi_0 (b + c (a + b)/mu) / (2 mu)``. Returns (unavailability, failure frequency),
    the frequency of entering state 2 being ``b pi_0 + c pi_1``. With ``b = 0`` this is the
    binomial ``(lambda/(lambda + mu))**2`` of two independent units.
    """
    mu = 1.0 / mttr
    a, b, c = 2.0 * rate_independent, rate_common, rate_independent + rate_common
    r1 = (a + b) / mu
    r2 = (b + c * r1) / (2.0 * mu)
    pi0 = 1.0 / (1.0 + r1 + r2)
    return r2 * pi0, b * pi0 + c * r1 * pi0
