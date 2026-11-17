"""Phase 4: identical vs diverse redundancy, cost against reliability.

Architectures of the navigation system differ in unit counts and in how many distinct
firmware images, network segments and suppliers each redundant group uses. Each is costed
with illustrative relative costs, quantified exactly, and compared on Pareto fronts across the
range of cyber exposure.
"""

from cyberccf.architecture_diversity_tradeoff.architectures import (
    Architecture,
    CostItem,
    cost,
    enumerate_architectures,
    load_costs,
    make_architecture,
    unreliability_at_scale,
)
from cyberccf.architecture_diversity_tradeoff.pareto import best_within_budget, pareto_front

__all__ = [
    "Architecture",
    "CostItem",
    "best_within_budget",
    "cost",
    "enumerate_architectures",
    "load_costs",
    "make_architecture",
    "pareto_front",
    "unreliability_at_scale",
]
