"""A small reduced ordered binary decision diagram (ROBDD) for exact quantification.

A BDD is Shannon decomposition stored as a graph: every node is ``if event then high else
low``, identical sub-functions are stored once, and redundant tests are removed (Bryant,
"Graph-based algorithms for Boolean function manipulation", IEEE Trans. Computers, 1986).
Fault-tree tools use it for exact probabilities because the probability of a node is

    P(node) = q_v P(high) + (1 - q_v) P(low),

a sum of non-negative terms, with no cancellation even for very small ``q`` (Rauzy, "New
algorithms for fault trees analysis", Reliability Engineering & System Safety 40, 1993).
Naive pivoting costs ``2**s`` for ``s`` shared events; the BDD shares the work that pivoting
repeats, which keeps groups with many common-cause events (26 for an alpha-factor group of
five) tractable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

FALSE, TRUE = 0, 1


class BDD:
    """A ROBDD manager over a fixed variable order (one variable per basic event)."""

    def __init__(self, order: Sequence[str]) -> None:
        self.order = list(order)
        self.level = {name: i for i, name in enumerate(self.order)}
        terminal = len(self.order)
        self.nodes: list[tuple[int, int, int]] = [(terminal, 0, 0), (terminal, 1, 1)]
        self._unique: dict[tuple[int, int, int], int] = {}
        self._ite: dict[tuple[int, int, int], int] = {}

    def _mk(self, var: int, low: int, high: int) -> int:
        if low == high:
            return low
        key = (var, low, high)
        node = self._unique.get(key)
        if node is None:
            node = len(self.nodes)
            self.nodes.append(key)
            self._unique[key] = node
        return node

    def var(self, name: str) -> int:
        """The function "event ``name`` occurs"."""
        return self._mk(self.level[name], FALSE, TRUE)

    def _cofactors(self, f: int, var: int) -> tuple[int, int]:
        v, low, high = self.nodes[f]
        return (low, high) if v == var else (f, f)

    def ite(self, f: int, g: int, h: int) -> int:
        """If ``f`` then ``g`` else ``h``."""
        if f == TRUE:
            return g
        if f == FALSE:
            return h
        if g == h:
            return g
        if g == TRUE and h == FALSE:
            return f
        key = (f, g, h)
        cached = self._ite.get(key)
        if cached is not None:
            return cached
        var = min(self.nodes[f][0], self.nodes[g][0], self.nodes[h][0])
        f0, f1 = self._cofactors(f, var)
        g0, g1 = self._cofactors(g, var)
        h0, h1 = self._cofactors(h, var)
        out = self._mk(var, self.ite(f0, g0, h0), self.ite(f1, g1, h1))
        self._ite[key] = out
        return out

    def not_(self, f: int) -> int:
        """Negation."""
        return self.ite(f, FALSE, TRUE)

    def and_(self, f: int, g: int) -> int:
        """Conjunction."""
        return self.ite(f, g, FALSE)

    def or_(self, f: int, g: int) -> int:
        """Disjunction."""
        return self.ite(f, TRUE, g)

    def at_least(self, k: int, fs: Sequence[int]) -> int:
        """True when at least ``k`` of the functions ``fs`` are true (threshold function)."""
        memo: dict[tuple[int, int], int] = {}

        def t(i: int, j: int) -> int:
            if j <= 0:
                return TRUE
            if len(fs) - i < j:
                return FALSE
            key = (i, j)
            if key not in memo:
                memo[key] = self.ite(fs[i], t(i + 1, j - 1), t(i + 1, j))
            return memo[key]

        return t(0, k)

    def probability(self, f: int, q: Mapping[str, float]) -> float:
        """``P(f is true)`` when each variable is true independently with probability ``q``."""
        memo = {FALSE: 0.0, TRUE: 1.0}

        def p(node: int) -> float:
            if node in memo:
                return memo[node]
            var, low, high = self.nodes[node]
            qv = q[self.order[var]]
            out = qv * p(high) + (1.0 - qv) * p(low)
            memo[node] = out
            return out

        return p(f)

    def size(self, f: int) -> int:
        """Number of internal nodes reachable from ``f``."""
        seen: set[int] = set()
        stack = [f]
        while stack:
            node = stack.pop()
            if node in (FALSE, TRUE) or node in seen:
                continue
            seen.add(node)
            _, low, high = self.nodes[node]
            stack += [low, high]
        return len(seen)
