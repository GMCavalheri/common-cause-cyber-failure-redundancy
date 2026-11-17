"""Reliability block diagrams in success logic: series, parallel and k-out-of-n blocks.

A block works when at least ``k`` of its children work. Series is ``k = n`` (every child must
work) and parallel is ``k = 1`` (one child is enough). A leaf is a component name, and the
same component may appear in several places (a power bus feeding two units), which is why
quantification in :mod:`cyberccf.independence_baseline.model` is exact for shared leaves.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Union

Block = Union[str, "KOutOfN"]


@dataclass(frozen=True)
class KOutOfN:
    """Works when at least ``k`` of ``children`` work."""

    k: int
    children: tuple[Block, ...]

    def __post_init__(self) -> None:
        if not self.children:
            raise ValueError("a block needs at least one child")
        if not 1 <= self.k <= len(self.children):
            raise ValueError(f"k = {self.k} must be between 1 and {len(self.children)}")


def Series(*children: Block) -> KOutOfN:
    """Every child must work."""
    return KOutOfN(len(children), tuple(children))


def Parallel(*children: Block) -> KOutOfN:
    """At least one child must work."""
    return KOutOfN(1, tuple(children))


def KofN(k: int, *children: Block) -> KOutOfN:
    """At least ``k`` children must work."""
    return KOutOfN(k, tuple(children))


def leaves(block: Block) -> list[str]:
    """Every leaf occurrence, left to right, with repeats (a shared leaf appears twice)."""
    if isinstance(block, str):
        return [block]
    out: list[str] = []
    for child in block.children:
        out.extend(leaves(child))
    return out


def components_in(block: Block) -> list[str]:
    """The distinct component names in the block, in first-seen order."""
    return list(dict.fromkeys(leaves(block)))


def at_least_k(k: int, p_work: Sequence[float]) -> float:
    """``P(at least k of the independent children work)``, children working with ``p_work``.

    The count of working children is Poisson-binomial; its distribution is built one child at
    a time (dynamic programming), which is exact and handles unequal probabilities.
    """
    dist = [1.0]  # dist[j] = P(j of the children seen so far work)
    for p in p_work:
        nxt = [0.0] * (len(dist) + 1)
        for j, d in enumerate(dist):
            nxt[j] += d * (1.0 - p)
            nxt[j + 1] += d * p
        dist = nxt
    return float(sum(dist[k:]))


def describe(block: Block) -> str:
    """A compact one-line rendering, e.g. ``series(parallel(a, b), c)``."""
    if isinstance(block, str):
        return block
    inner = ", ".join(describe(c) for c in block.children)
    n = len(block.children)
    if block.k == n and n > 1:
        return f"series({inner})"
    if block.k == 1 and n > 1:
        return f"parallel({inner})"
    if n == 1:
        return inner
    return f"{block.k}-of-{n}({inner})"
