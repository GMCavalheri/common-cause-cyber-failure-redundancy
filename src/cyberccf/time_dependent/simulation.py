"""Monte Carlo oracles: simulated missions and a discrete-event simulation with repair.

Both simulations share nothing with the exact engines except the model description, so
agreement within their confidence intervals is independent evidence that the BDD and the
Markov chain are right.

* :func:`simulate_missions` samples whether each basic event occurs during a mission
  (probability ``1 - exp(-lambda t)``), fails the components it covers, and evaluates the
  block diagram on the sampled states, vectorised over missions. The estimate comes with a
  Wilson score interval (Wilson, 1927).
* :func:`simulate_availability` runs a discrete-event simulation of the repairable system:
  every basic event is a Poisson process, every failed component is repaired after an
  exponential time with its own mean. It reports the fraction of time down and the number of
  system failures per hour, over independent replications (seeded child generators), with a
  Student-t interval across replications.
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats

from cyberccf.independence_baseline.model import Model, works_with_failed
from cyberccf.independence_baseline.structure import Block


@dataclass(frozen=True)
class Estimate:
    """A Monte Carlo estimate and its confidence interval."""

    value: float
    low: float
    high: float

    def covers(self, x: float) -> bool:
        """Is ``x`` inside the interval?"""
        return self.low <= x <= self.high


def wilson(successes: int, n: int, z: float = 3.0) -> Estimate:
    """Wilson score interval for a binomial proportion (z = 3 by default: about 99.7 %)."""
    p = successes / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return Estimate(p, max(0.0, centre - half), min(1.0, centre + half))


def _works(block: Block, failed: Mapping[str, NDArray[np.bool_]]) -> NDArray[np.bool_]:
    if isinstance(block, str):
        return ~failed[block]
    count = sum(_works(c, failed).astype(np.int64) for c in block.children)
    return np.asarray(count >= block.k)


def simulate_missions(
    model: Model, hours: float, n: int, rng: np.random.Generator, z: float = 3.0
) -> Estimate:
    """Fraction of ``n`` simulated missions in which the system fails, with a Wilson interval."""
    q = model.probabilities(hours)
    occurred = {e: rng.random(n) < p for e, p in q.items()}
    failed = {
        c: np.any(np.stack([occurred[e] for e in model.causes[c]]), axis=0)
        for c in model.components
    }
    down = ~_works(model.structure, failed)
    return wilson(int(down.sum()), n, z)


@dataclass(frozen=True)
class AvailabilityEstimate:
    """Simulated unavailability and system failure frequency."""

    unavailability: Estimate
    failure_frequency: Estimate


def _replication(
    model: Model, mttr: Mapping[str, float], horizon: float, rng: np.random.Generator
) -> tuple[float, int]:
    """One run from all-up: (time down, number of up -> down transitions)."""
    events = [(e.name, e.rate_per_hour, model.affected(e.name)) for e in model.events]
    heap: list[tuple[float, int, int]] = []  # (time, kind 0 = event / 1 = repair, index)
    for i, (_, rate, _) in enumerate(events):
        if rate > 0:
            heapq.heappush(heap, (rng.exponential(1.0 / rate), 0, i))
    comps = list(model.components)
    failed: set[str] = set()
    t, down_time, failures = 0.0, 0.0, 0
    is_up = True
    while heap:
        when, kind, i = heapq.heappop(heap)
        if when > horizon:
            break
        if not is_up:
            down_time += when - t
        t = when
        if kind == 0:
            _, rate, affected = events[i]
            for c in affected:
                if c not in failed:
                    failed.add(c)
                    heapq.heappush(heap, (t + rng.exponential(mttr[c]), 1, comps.index(c)))
            heapq.heappush(heap, (t + rng.exponential(1.0 / rate), 0, i))
        else:
            failed.discard(comps[i])
        now_up = works_with_failed(model, failed)
        if is_up and not now_up:
            failures += 1
        is_up = now_up
    if not is_up:
        down_time += horizon - t
    return down_time, failures


def simulate_availability(
    model: Model,
    mttr: Mapping[str, float],
    horizon: float,
    replications: int,
    rng: np.random.Generator,
    confidence: float = 0.997,
) -> AvailabilityEstimate:
    """Unavailability and failure frequency over independent replications of ``horizon`` hours."""
    if replications < 2:
        raise ValueError("need at least two replications for an interval")
    runs = [_replication(model, mttr, horizon, child) for child in rng.spawn(replications)]
    u = np.array([d / horizon for d, _ in runs])
    w = np.array([f / horizon for _, f in runs])
    tq = float(stats.t.ppf(0.5 + confidence / 2, replications - 1))

    def interval(x: NDArray[np.float64]) -> Estimate:
        m, se = float(x.mean()), float(x.std(ddof=1) / math.sqrt(len(x)))
        return Estimate(m, m - tq * se, m + tq * se)

    return AvailabilityEstimate(interval(u), interval(w))
