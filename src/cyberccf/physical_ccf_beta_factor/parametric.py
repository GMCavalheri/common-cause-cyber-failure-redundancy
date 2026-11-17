"""Parametric common-cause models: basic parameter, beta factor, MGL and alpha factor.

All three parametric models of NUREG/CR-5485 (Mosleh, Rasmuson & Marshall, 1998, section 5.4)
are re-parameterisations of the **basic parameter model**. In a common-cause component group
(CCCG) of ``m`` identical components, ``Q_k`` is the probability of a basic event that fails
``k`` *specific* components (and no others). A component belongs to ``C(m-1, k-1)`` events of
size ``k``, so its total failure probability is

    Q_t = sum_k C(m-1, k-1) Q_k                         (NUREG/CR-5485, Eq. 5.2 generalised)

Each model below returns the **fractions** ``f_k = Q_k / Q_t`` for ``k = 1..m``; they always
satisfy ``sum_k C(m-1, k-1) f_k = 1``.

* **Beta factor** (Fleming, 1975): a fraction ``beta`` of each component's failures fail the
  whole group; the rest are independent. ``f_1 = 1 - beta``, ``f_m = beta``, others 0.
* **Multiple Greek letter** (NUREG/CR-5485, Eq. 5.11 for ``m = 3``): ``rho_1 = 1``,
  ``rho_2 = beta``, ``rho_3 = gamma``, ``rho_4 = delta``, ... with ``rho_{m+1} = 0``, and
  ``f_k = (prod_{i<=k} rho_i)(1 - rho_{k+1}) / C(m-1, k-1)``. Beta is MGL with every further
  letter equal to 1.
* **Alpha factor** (NUREG/CR-5485, Eqs. 5.6-5.9): ``alpha_k`` is the fraction of failure
  *events* in the group that involve exactly ``k`` components. With staggered testing
  ``f_k = alpha_k / C(m-1, k-1)``; with non-staggered testing
  ``f_k = k alpha_k / (C(m-1, k-1) alpha_t)``, ``alpha_t = sum_k k alpha_k``.

The beta factor applies to rates as well as probabilities, and this project applies the
fractions to rates: a member with total rate ``lambda_t`` gets an independent event at
``f_1 lambda_t`` and each size-``k`` event occurs at ``f_k lambda_t``. Because the member's
events are independent Poisson processes, its total failure probability over ``t`` hours is
exactly ``1 - exp(-lambda_t t)``, the same as without common cause: CCF moves probability
between cut sets, it does not add failures to a component.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import comb, isclose, prod


def _check_fraction(name: str, x: float) -> None:
    if not 0.0 <= x <= 1.0:
        raise ValueError(f"{name} must be in [0, 1], got {x}")


def check_fractions(m: int, f: Sequence[float]) -> None:
    """Raise unless ``f`` has ``m`` non-negative entries with ``sum C(m-1,k-1) f_k = 1``."""
    if len(f) != m:
        raise ValueError(f"expected {m} fractions, got {len(f)}")
    if any(x < 0 for x in f):
        raise ValueError("fractions must be non-negative")
    total = sum(comb(m - 1, k - 1) * fk for k, fk in enumerate(f, start=1))
    if not isclose(total, 1.0, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(f"sum C(m-1,k-1) f_k must be 1, got {total}")


def independent_fractions(m: int) -> list[float]:
    """No common cause: every failure is independent."""
    return [1.0] + [0.0] * (m - 1)


def beta_factor_fractions(m: int, beta: float) -> list[float]:
    """Beta factor: ``f_1 = 1 - beta``, ``f_m = beta``."""
    if m < 2:
        raise ValueError("a common-cause group needs at least two members")
    _check_fraction("beta", beta)
    f = [0.0] * m
    f[0] += 1.0 - beta
    f[m - 1] += beta
    return f


def mgl_fractions(m: int, letters: Sequence[float]) -> list[float]:
    """Multiple Greek letter: ``letters = (beta, gamma, delta, ...)``, ``m - 1`` of them."""
    if m < 2:
        raise ValueError("a common-cause group needs at least two members")
    if len(letters) != m - 1:
        raise ValueError(f"MGL for m = {m} needs {m - 1} letters, got {len(letters)}")
    for i, x in enumerate(letters):
        _check_fraction(f"letter {i + 2}", x)
    rho = [1.0, *letters, 0.0]  # rho_1 .. rho_{m+1}
    return [prod(rho[:k]) * (1.0 - rho[k]) / comb(m - 1, k - 1) for k in range(1, m + 1)]


def alpha_fractions(m: int, alphas: Sequence[float], staggered: bool) -> list[float]:
    """Alpha factor fractions for staggered or non-staggered testing (NUREG/CR-5485)."""
    if len(alphas) != m:
        raise ValueError(f"alpha factor for m = {m} needs {m} alphas, got {len(alphas)}")
    if any(a < 0 for a in alphas) or not isclose(sum(alphas), 1.0, rel_tol=1e-12):
        raise ValueError("alphas must be non-negative and sum to 1")
    if staggered:
        return [a / comb(m - 1, k - 1) for k, a in enumerate(alphas, start=1)]
    alpha_t = sum(k * a for k, a in enumerate(alphas, start=1))
    return [k * a / (comb(m - 1, k - 1) * alpha_t) for k, a in enumerate(alphas, start=1)]


def alphas_from_fractions(m: int, f: Sequence[float], staggered: bool) -> list[float]:
    """Invert :func:`alpha_fractions`: the alpha factors that give the fractions ``f``.

    Staggered: ``alpha_k = C(m-1, k-1) f_k``. Non-staggered: ``alpha_k`` is the share of
    events of size ``k``, ``C(m, k) Q_k / sum_j C(m, j) Q_j`` (the alpha definition).
    """
    check_fractions(m, f)
    if staggered:
        return [comb(m - 1, k - 1) * fk for k, fk in enumerate(f, start=1)]
    counts = [comb(m, k) * fk for k, fk in enumerate(f, start=1)]
    total = sum(counts)
    return [c / total for c in counts]


def beta_equivalent(m: int, f: Sequence[float]) -> float:
    """The MGL ``beta``: probability that a member's failure is shared with another member.

    ``beta = 1 - f_1``, because ``f_1`` is the share of a member's failures that are its own.
    """
    check_fractions(m, f)
    return 1.0 - f[0]
