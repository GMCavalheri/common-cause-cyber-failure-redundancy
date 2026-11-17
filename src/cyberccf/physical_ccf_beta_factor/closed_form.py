"""Closed forms for common-cause groups, used as oracles and in Lesson 2.

Rates are split as in :mod:`~cyberccf.physical_ccf_beta_factor.parametric`: with total rate
``lambda`` and beta factor ``beta``, the independent part occurs at ``(1 - beta) lambda`` and
the common-cause event at ``beta lambda``, all independent Poisson processes.
"""

from __future__ import annotations

import math


def beta_split(rate: float, beta: float, hours: float) -> tuple[float, float]:
    """``(q_independent, q_ccf)`` over a mission of ``hours``."""
    return -math.expm1(-(1.0 - beta) * rate * hours), -math.expm1(-beta * rate * hours)


def one_of_m_beta_unreliability(m: int, rate: float, beta: float, hours: float) -> float:
    """A 1-of-m group fails if the CCF event occurs or all m independent parts fail.

    ``Q = 1 - (1 - q_c)(1 - q_i**m) = q_c + (1 - q_c) q_i**m``. As ``m`` grows,
    ``Q -> q_c ~ beta lambda t``: the floor that no amount of identical redundancy goes below.
    The second form is the one computed: the first loses relative precision to cancellation
    when ``Q`` is tiny.
    """
    q_i, q_c = beta_split(rate, beta, hours)
    return q_c + (1.0 - q_c) * q_i**m


def two_of_three_rare_event(q1: float, q2: float, q3: float) -> float:
    """NUREG/CR-5485 Eq. 5.5: a 2-of-3 system fails with ``Q_s ~ 3 Q_1**2 + 3 Q_2 + Q_3``."""
    return 3.0 * q1**2 + 3.0 * q2 + q3


def ccf_floor(rate: float, beta: float, hours: float) -> float:
    """The unreliability a 1-of-m beta group can never go below: ``1 - exp(-beta lambda t)``."""
    return -math.expm1(-beta * rate * hours)
