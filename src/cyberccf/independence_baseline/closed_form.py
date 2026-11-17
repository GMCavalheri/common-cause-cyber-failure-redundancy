"""Closed forms for independent components, used as test oracles and in the lessons.

Every formula assumes mutually independent failures (the assumption the rest of the project
corrects). ``q`` is a failure probability over the mission, ``p = 1 - q`` a success probability.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def series_unreliability(q: Sequence[float]) -> float:
    """A series system fails unless every component survives: ``1 - prod(1 - q_i)``."""
    return 1.0 - math.prod(1.0 - x for x in q)


def parallel_unreliability(q: Sequence[float]) -> float:
    """A parallel system fails only if every component fails: ``prod(q_i)``."""
    return math.prod(q)


def k_of_n_reliability(k: int, n: int, p: float) -> float:
    """``P(at least k of n identical independent units work)``, the binomial tail."""
    return sum(math.comb(n, j) * p**j * (1.0 - p) ** (n - j) for j in range(k, n + 1))


def one_of_n_unreliability(n: int, q: float) -> float:
    """A 1-of-n group of identical independent channels fails with probability ``q**n``."""
    return q**n


def navigation_unreliability(q_egi: float, q_power: float, q_bus: float, q_mc: float) -> float:
    """The 2-EGI, 2-bus navigation system, derived by hand by conditioning on the power buses.

    The power buses are the only shared leaves. Given both up, the source group fails with
    ``q_egi**2``; given exactly one up (probability ``2 q_power (1 - q_power)``), only one EGI is
    powered and the group fails with ``q_egi``; given both down, everything fails. The bus pair
    and the mission computer are independent of that conditioning::

        R = (1 - q_bus**2)(1 - q_mc)[(1 - q_power)**2 (1 - q_egi**2)
                                     + 2 q_power (1 - q_power)(1 - q_egi)]
    """
    sources_and_power = (1.0 - q_power) ** 2 * (1.0 - q_egi**2) + 2.0 * q_power * (
        1.0 - q_power
    ) * (1.0 - q_egi)
    return 1.0 - (1.0 - q_bus**2) * (1.0 - q_mc) * sources_and_power
