"""Phase 1: what redundancy is claimed to buy when channels are assumed independent."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt

from cyberccf import plotting
from cyberccf.independence_baseline import (
    MISSION_HOURS,
    BasicEvent,
    component_specs,
    describe,
    minimal_cut_sets,
    navigation_model,
    unreliability,
)

from common import FIGURES, table, write_result


def main() -> None:
    specs = component_specs()
    params = table(
        ["component", "λ (per hour)", "q over 10 h", "basis"],
        [
            [
                s.name,
                s.failure_rate_per_hour,
                BasicEvent(s.name, s.failure_rate_per_hour).probability(MISSION_HOURS),
                s.basis.replace("copied from CPS-01 (cyberrel v1.0.0) system_parameters.csv: ", ""),
            ]
            for s in specs.values()
        ],
    )

    base = navigation_model()
    q = base.probabilities(MISSION_HOURS)
    cuts = sorted(
        minimal_cut_sets(base),
        key=lambda c: -math.prod(q[e] for e in c),
    )
    total = unreliability(base, MISSION_HOURS)
    cut_rows = [
        [
            " + ".join(sorted(c)),
            len(c),
            math.prod(q[e] for e in c),
            math.prod(q[e] for e in c) / total,
        ]
        for c in cuts
    ]
    cut_table = table(
        ["minimal cut set", "order", "probability (10 h)", "share of system unreliability"],
        cut_rows,
    )

    # The claimed value of adding EGIs and bus channels, under independence.
    egi_counts, bus_counts = [1, 2, 3, 4], [1, 2, 3]
    grid = {
        (n, m): unreliability(navigation_model(n, m), MISSION_HOURS)
        for n in egi_counts
        for m in bus_counts
    }
    redundancy = table(
        ["EGI units", *[f"{m} bus channel(s)" for m in bus_counts]],
        [[n, *[grid[(n, m)] for m in bus_counts]] for n in egi_counts],
    )

    dual = navigation_model(mission_computers=2)
    dual_total = unreliability(dual, MISSION_HOURS)
    qd = dual.probabilities(MISSION_HOURS)
    dual_cuts = table(
        ["minimal cut set", "order", "probability (10 h)", "share of system unreliability"],
        [
            [
                " + ".join(sorted(c)),
                len(c),
                math.prod(qd[e] for e in c),
                math.prod(qd[e] for e in c) / dual_total,
            ]
            for c in sorted(minimal_cut_sets(dual), key=lambda c: -math.prod(qd[e] for e in c))
        ],
    )

    q_egi = q["egi_1"]
    one_of_n = table(
        ["channels n", "1-of-n unreliability q^n", "improvement over one channel"],
        [[n, q_egi**n, q_egi / q_egi**n] for n in (1, 2, 3, 4)],
    )

    summary = table(
        ["quantity", "value"],
        [
            ["structure", f"`{describe(base.structure)}`"],
            ["mission (h)", MISSION_HOURS],
            ["P(loss of navigation), independence, 2 EGI + 2 bus channels", total],
            ["the same with 1 EGI + 1 bus channel", grid[(1, 1)]],
            ["claimed benefit of the redundancy (ratio)", grid[(1, 1)] / total],
            ["share carried by the single mission computer", q["mission_computer"] / total],
            [
                "P(loss of navigation), independence, with two mission computers",
                dual_total,
            ],
            ["claimed benefit of the second mission computer (ratio)", total / dual_total],
        ],
    )

    plotting.use_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8))
    ns = [1, 2, 3, 4, 5, 6]
    ax1.semilogy(ns, [q_egi**n for n in ns], "o-", color=plotting.INDEPENDENT_COLOR)
    ax1.set_xlabel("identical channels n (1-of-n)")
    ax1.set_ylabel("P(all channels fail in 10 h)")
    ax1.set_title("One EGI channel group, independence: q^n")
    curves = [
        ("1 bus channel", [grid[(n, 1)] for n in egi_counts]),
        ("2 bus channels", [grid[(n, 2)] for n in egi_counts]),
        (
            "2 bus channels, 2 mission computers",
            [
                unreliability(navigation_model(n, 2, mission_computers=2), MISSION_HOURS)
                for n in egi_counts
            ],
        ),
    ]
    for (label, values), color in zip(curves, plotting.SERIES_COLORS, strict=False):
        ax2.semilogy(egi_counts, values, "o-", color=color, label=label)
    ax2.set_xlabel("EGI units")
    ax2.set_ylabel("P(loss of navigation in 10 h)")
    ax2.set_title("Navigation system, independence")
    ax2.legend(fontsize=8)
    for ax in (ax1, ax2):
        ax.xaxis.get_major_locator().set_params(integer=True)
    fig.subplots_adjust(wspace=0.35)
    fig.savefig(FIGURES / "independence_baseline.png")
    plt.close(fig)

    write_result(
        "independence",
        "Phase 1: the independence baseline",
        [
            ("Summary", summary),
            ("Parameters (all assumptions, copied from CPS-01)", params),
            ("Minimal cut sets, ranked by probability", cut_table),
            ("With two mission computers: minimal cut sets", dual_cuts),
            ("One channel group: what independence promises", one_of_n),
            ("Navigation system: claimed value of more redundancy", redundancy),
        ],
    )


if __name__ == "__main__":
    main()
