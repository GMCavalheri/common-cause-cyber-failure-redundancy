"""Phase 4: what diversity buys, what it costs, and how the answer moves with the exposure."""

from __future__ import annotations

import matplotlib.pyplot as plt

from cyberccf import plotting
from cyberccf.architecture_diversity_tradeoff import (
    best_within_budget,
    cost,
    enumerate_architectures,
    load_costs,
    make_architecture,
    pareto_front,
    unreliability_at_scale,
)
from cyberccf.independence_baseline import MISSION_HOURS

from common import FIGURES, table, write_result

SCALES = [0.0, 0.25, 1.0, 4.0, 10.0]
BUDGETS = [0.0, 15.0, 25.0, 35.0, 50.0, 80.0, 120.0]


def main() -> None:
    costs = load_costs()
    cost_table = table(
        ["item", "group", "relative cost", "basis"],
        [[c.item, c.component_group, c.cost, c.basis] for c in costs.values()],
    )

    archs = list(enumerate_architectures())
    models = {a: a.model() for a in archs}
    q = {s: {a: unreliability_at_scale(models[a], MISSION_HOURS, s) for a in archs} for s in SCALES}
    c = {a: cost(a, costs) for a in archs}
    points = {s: [(c[a], q[s][a], a) for a in archs] for s in SCALES}

    front = pareto_front(points[1.0])
    front_table = table(
        ["cost", "P(loss of navigation, 10 h)", "architecture"],
        [[p[0], p[1], p[2].label] for p in front],
    )

    # Single changes from two identical EGIs and two identical computers.
    base = make_architecture(2, 2)
    changes = {
        "third identical EGI": make_architecture(3, 2),
        "2nd EGI firmware image": make_architecture(2, 2, {("nav_source", "firmware"): 2}),
        "2nd EGI network segment": make_architecture(2, 2, {("nav_source", "network"): 2}),
        "2nd EGI supplier": make_architecture(2, 2, {("nav_source", "supply_chain"): 2}),
        "2nd computer software load": make_architecture(
            2, 2, {("mission_computer", "firmware"): 2}
        ),
        "2nd computer network segment": make_architecture(
            2, 2, {("mission_computer", "network"): 2}
        ),
        "2nd computer supplier": make_architecture(2, 2, {("mission_computer", "supply_chain"): 2}),
    }
    rows = []
    rank_rows = []
    for s in SCALES:
        values = {name: (q[s][base] - q[s][a]) / (c[a] - c[base]) for name, a in changes.items()}
        ranked = sorted(values, key=lambda n: -values[n])
        rank_rows.append([s, *[f"{i + 1}. {n}" for i, n in enumerate(ranked[:3])]])
        for name, a in changes.items():
            if s in (0.25, 1.0, 10.0):
                rows.append([s, name, c[a] - c[base], q[s][base] - q[s][a], values[name]])
    single = table(
        [
            "exposure scale",
            "change",
            "added cost",
            "reduction in P(loss)",
            "reduction per cost unit",
        ],
        rows,
    )
    ranking = table(["exposure scale", "best value", "second", "third"], rank_rows)

    budget_rows = []
    for s in (0.0, 1.0, 10.0):
        for b in BUDGETS:
            best = best_within_budget(points[s], b)
            assert best is not None
            budget_rows.append([s, b, best[0], best[1], best[2].label])
    budget = table(
        ["exposure scale", "budget", "cost", "P(loss of navigation)", "best architecture"],
        budget_rows,
    )

    # The two headline designs against the baseline, over the whole range.
    third = make_architecture(3, 2)
    full = make_architecture(
        2,
        2,
        {
            (g, d): 2
            for g in ("nav_source", "mission_computer")
            for d in ("firmware", "network", "supply_chain")
        },
    )
    cheap = make_architecture(
        2, 2, {("nav_source", "network"): 2, ("mission_computer", "network"): 2}
    )
    vs = table(
        [
            "exposure scale",
            "2 EGI + 2 MC identical",
            "third identical EGI",
            "both segments split (cost 4)",
            f"fully diverse pairs (cost {c[full] - c[base]:.0f})",
        ],
        [[s, q[s][base], q[s][third], q[s][cheap], q[s][full]] for s in SCALES],
    )

    plotting.use_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.9))
    for n_mc, color in [(1, plotting.NEUTRAL_COLOR), (2, plotting.INDEPENDENT_COLOR)]:
        sel = [p for p in points[1.0] if p[2].mission_computers == n_mc]
        ax1.scatter(
            [p[0] for p in sel],
            [p[1] for p in sel],
            s=10,
            alpha=0.5,
            color=color,
            label=f"{n_mc} mission computer(s)",
        )
    ax1.step(
        [p[0] for p in front],
        [p[1] for p in front],
        where="post",
        color=plotting.CYBER_COLOR,
        label="Pareto front",
    )
    ax1.set_yscale("log")
    ax1.set_xlabel("relative cost (illustrative)")
    ax1.set_ylabel("P(loss of navigation in 10 h)")
    ax1.set_title("315 designs at the illustrative exposure")
    ax1.legend(fontsize=8)
    for s, color in zip(SCALES, plotting.SERIES_COLORS, strict=True):
        f = pareto_front(points[s])
        ax2.step(
            [p[0] for p in f],
            [p[1] for p in f],
            where="post",
            color=color,
            label=f"exposure × {s:g}",
        )
    ax2.set_yscale("log")
    ax2.set_xlabel("relative cost (illustrative)")
    ax2.set_ylabel("P(loss of navigation in 10 h)")
    ax2.set_title("Pareto fronts across the exposure range")
    ax2.legend(fontsize=8)
    fig.subplots_adjust(wspace=0.35)
    fig.savefig(FIGURES / "diversity_tradeoff.png")
    plt.close(fig)

    write_result(
        "diversity",
        "Phase 4: architecture diversity trade-off",
        [
            ("Relative costs (illustrative assumptions, no real cost data)", cost_table),
            ("Pareto front at the illustrative exposure", front_table),
            ("Single changes from two identical EGIs and two identical computers", single),
            ("Which single change buys the most per cost unit", ranking),
            ("Best design within a budget", budget),
            ("Headline designs across the exposure range", vs),
        ],
    )


if __name__ == "__main__":
    main()
