"""Closed forms for a group of channels with physical and cyber common cause.

A 1-of-m group of channels, each with physical rate ``lambda_p`` split by the physical beta
factor ``beta_p`` and a cyber exposure ``lambda_c`` (the sum of its attribute rates). The
derivations are in ``docs/derivation.md``; the tests check each form against the exact engine.
"""

from __future__ import annotations

import math


def cyber_beta_from_rates(physical_rate: float, cyber_rate: float) -> float:
    """``beta_c = lambda_c / (lambda_p + lambda_c)`` for identical channels."""
    total = physical_rate + cyber_rate
    return 0.0 if total == 0 else cyber_rate / total


def cyber_rate_from_beta(physical_rate: float, beta_c: float) -> float:
    """The cyber rate giving cyber beta ``beta_c``: ``lambda_p beta_c / (1 - beta_c)``."""
    if not 0.0 <= beta_c < 1.0:
        raise ValueError("beta_c must be in [0, 1)")
    return physical_rate * beta_c / (1.0 - beta_c)


def combined_beta(beta_p: float, beta_c: float) -> float:
    """The effective beta of identical channels: ``1 - (1 - beta_p)(1 - beta_c)``.

    A failure is independent only if it is physical (share ``1 - beta_c``) *and* not a
    physical common cause (share ``1 - beta_p``).
    """
    return 1.0 - (1.0 - beta_p) * (1.0 - beta_c)


def identical_group_unreliability(
    m: int, physical_rate: float, beta_p: float, cyber_rate: float, hours: float
) -> float:
    """1-of-m identical channels: one common event at ``beta_p lambda_p + lambda_c``.

    ``Q = q_cc + (1 - q_cc) q_i**m`` with ``q_i = 1 - exp(-(1 - beta_p) lambda_p t)``.
    """
    q_i = -math.expm1(-(1.0 - beta_p) * physical_rate * hours)
    q_cc = -math.expm1(-(beta_p * physical_rate + cyber_rate) * hours)
    return q_cc + (1.0 - q_cc) * q_i**m


def diverse_group_unreliability(
    m: int, physical_rate: float, beta_p: float, cyber_rate: float, hours: float
) -> float:
    """1-of-m fully diverse channels: cyber exposure becomes each channel's own failure.

    ``Q = q_cc + (1 - q_cc) q_i**m`` with ``q_cc = 1 - exp(-beta_p lambda_p t)`` and
    ``q_i = 1 - exp(-((1 - beta_p) lambda_p + lambda_c) t)``.
    """
    q_i = -math.expm1(-((1.0 - beta_p) * physical_rate + cyber_rate) * hours)
    q_cc = -math.expm1(-beta_p * physical_rate * hours)
    return q_cc + (1.0 - q_cc) * q_i**m


def split_gain(k: float, p_u: float, p_v: float, p_uv: float) -> float:
    """Drop in P(group fails) when one shared event is split in two (Proposition 3).

    A parallel group's members are split into subsets A and B. ``U`` (``V``) is the event that
    every member of A (B) fails from its other causes; ``k`` is the probability of the shared
    event. Replacing it by two independent events of the same probability, one per subset,
    lowers P(all fail) by exactly ``k (1 - k) P(not U and not V)``, which is never negative.
    """
    return k * (1.0 - k) * (1.0 - p_u - p_v + p_uv)
