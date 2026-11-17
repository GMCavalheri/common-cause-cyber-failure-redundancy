"""Pareto fronts and the value of single design changes."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def pareto_front(points: Sequence[tuple[float, float, T]]) -> list[tuple[float, float, T]]:
    """Non-dominated points when both coordinates are to be minimised (cost, unreliability).

    A point is dominated if another is no worse in both coordinates and better in one. Ties
    in both coordinates keep the first. Sorted by cost, the front's unreliability strictly
    decreases.
    """
    ordered = sorted(enumerate(points), key=lambda ip: (ip[1][0], ip[1][1], ip[0]))
    front: list[tuple[float, float, T]] = []
    best = float("inf")
    for _, p in ordered:
        if p[1] < best:
            front.append(p)
            best = p[1]
    return front


def best_within_budget(
    points: Sequence[tuple[float, float, T]], budget: float
) -> tuple[float, float, T] | None:
    """The least unreliable point that costs at most ``budget`` (ties: the cheaper)."""
    feasible = [p for p in points if p[0] <= budget]
    if not feasible:
        return None
    return min(feasible, key=lambda p: (p[1], p[0]))
