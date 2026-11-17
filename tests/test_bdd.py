"""The BDD against truth tables: every operation and every probability, exhaustively."""

from __future__ import annotations

import math
from itertools import product

import pytest
from hypothesis import given
from hypothesis import strategies as st

from cyberccf.independence_baseline.bdd import BDD, FALSE, TRUE

NAMES = ["a", "b", "c", "d"]


def evaluate(bdd: BDD, f: int, assignment: dict[str, bool]) -> bool:
    while f not in (FALSE, TRUE):
        var, low, high = bdd.nodes[f]
        f = high if assignment[bdd.order[var]] else low
    return f == TRUE


@st.composite
def formulas(draw: st.DrawFn, depth: int = 3) -> tuple[str, object]:
    if depth == 0 or draw(st.booleans()):
        return ("var", draw(st.sampled_from(NAMES)))
    op = draw(st.sampled_from(["and", "or", "not", "atleast"]))
    if op == "not":
        return ("not", draw(formulas(depth - 1)))
    if op == "atleast":
        kids = [draw(formulas(depth - 1)) for _ in range(draw(st.integers(1, 3)))]
        return ("atleast", (draw(st.integers(0, len(kids) + 1)), kids))
    return (op, (draw(formulas(depth - 1)), draw(formulas(depth - 1))))


def build(bdd: BDD, f: tuple[str, object]) -> int:
    op, arg = f
    if op == "var":
        return bdd.var(arg)  # type: ignore[arg-type]
    if op == "not":
        return bdd.not_(build(bdd, arg))  # type: ignore[arg-type]
    if op == "atleast":
        k, kids = arg  # type: ignore[misc]
        return bdd.at_least(k, [build(bdd, x) for x in kids])
    left, right = arg  # type: ignore[misc]
    g, h = build(bdd, left), build(bdd, right)
    return bdd.and_(g, h) if op == "and" else bdd.or_(g, h)


def truth(f: tuple[str, object], a: dict[str, bool]) -> bool:
    op, arg = f
    if op == "var":
        return a[arg]  # type: ignore[index]
    if op == "not":
        return not truth(arg, a)  # type: ignore[arg-type]
    if op == "atleast":
        k, kids = arg  # type: ignore[misc]
        return sum(truth(x, a) for x in kids) >= k
    left, right = arg  # type: ignore[misc]
    return truth(left, a) and truth(right, a) if op == "and" else truth(left, a) or truth(right, a)


@given(formulas(), st.lists(st.floats(0.0, 1.0), min_size=4, max_size=4))
def test_bdd_matches_the_truth_table_and_its_probability(
    f: tuple[str, object], qs: list[float]
) -> None:
    bdd = BDD(NAMES)
    node = build(bdd, f)
    q = dict(zip(NAMES, qs, strict=True))
    expected = 0.0
    for values in product((False, True), repeat=4):
        a = dict(zip(NAMES, values, strict=True))
        assert evaluate(bdd, node, a) == truth(f, a)
        if truth(f, a):
            expected += math.prod(q[n] if a[n] else 1 - q[n] for n in NAMES)
    assert bdd.probability(node, q) == pytest.approx(expected, abs=1e-12)


def test_reduction_shares_nodes() -> None:
    bdd = BDD(NAMES)
    a, b = bdd.var("a"), bdd.var("b")
    assert bdd.and_(a, b) == bdd.and_(b, a)  # canonical: one node per function
    assert bdd.or_(a, bdd.not_(a)) == TRUE
    assert bdd.and_(a, bdd.not_(a)) == FALSE
    assert bdd.size(bdd.at_least(2, [bdd.var(n) for n in NAMES])) == 6  # 2-of-4 threshold
    assert bdd.size(TRUE) == 0


def test_tiny_probabilities_keep_full_relative_precision() -> None:
    # P(a and b) = 1e-20 exactly: no 1 - (1 - x) cancellation on the way.
    bdd = BDD(NAMES)
    f = bdd.and_(bdd.var("a"), bdd.var("b"))
    assert bdd.probability(f, {"a": 1e-10, "b": 1e-10, "c": 0.5, "d": 0.5}) == pytest.approx(
        1e-20, rel=1e-15
    )
