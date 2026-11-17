"""Phase 2: how physical common cause caps what identical redundancy can buy."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np

from cyberccf import plotting
from cyberccf.independence_baseline import (
    MISSION_HOURS,
    KofN,
    independent_model,
    minimal_cut_sets,
    navigation_model,
    unreliability,
)
from cyberccf.physical_ccf_beta_factor import (
    CCFGroup,
    apply_ccf,
    ccf_floor,
    load_ccf_parameters,
    mgl_fractions,
    one_of_m_beta_unreliability,
    physical_ccf_model,
)

from common import FIGURES, table, write_result

RATE = 2e-4  # one EGI (assumption, CPS-01/02)
BETAS = [0.0, 0.01, 0.02, 0.05, 0.1]
MS = [1, 2, 3, 4, 5, 6]


def group_model(m: int, k: int, fractions: list[float]) -> float:
    names = [f"u{i}" for i in range(m)]
    base = independent_model("g", KofN(k, *names), dict.fromkeys(names, RATE))
    if m == 1:
        return unreliability(base, MISSION_HOURS)
    return unreliability(
        apply_ccf(base, CCFGroup("g", tuple(names), tuple(fractions))), MISSION_HOURS
    )


def main() -> None:
    rows = load_ccf_parameters()
    params = table(
        ["component group", "CCF group", "β", "basis"],
        [[r.component_group, r.group, r.beta, r.basis] for r in rows.values()],
    )

    # One group of identical EGIs: the cap.
    grid = {
        (b, m): one_of_m_beta_unreliability(m, RATE, b, MISSION_HOURS) for b in BETAS for m in MS
    }
    cap = table(
        ["β", *[f"m = {m}" for m in MS], "floor 1 − e^(−βλt)"],
        [[b, *[grid[(b, m)] for m in MS], ccf_floor(RATE, b, MISSION_HOURS)] for b in BETAS],
    )
    single = grid[(0.0, 1)]
    gain = table(
        ["β", "gain of the 2nd unit", "gain of the 3rd unit", "best possible gain (m → ∞)"],
        [
            [
                b,
                single / grid[(b, 2)],
                grid[(b, 2)] / grid[(b, 3)],
                math.inf if b == 0 else single / ccf_floor(RATE, b, MISSION_HOURS),
            ]
            for b in BETAS
        ],
    )

    # Beta vs MGL for three units, the same beta: what the extra letter changes.
    beta, gammas = 0.02, [1.0, 0.5, 0.1]
    mgl_rows = []
    for k, label in [(1, "1-of-3"), (2, "2-of-3")]:
        ind = group_model(3, k, [1.0, 0.0, 0.0])
        mgl_rows.append(
            [label, ind, *[group_model(3, k, mgl_fractions(3, [beta, g])) for g in gammas]]
        )
    mgl = table(
        ["3 EGIs", "independent", *[f"MGL β = 0.02, γ = {g}" for g in gammas]],
        mgl_rows,
    )

    # The navigation system.
    nav = []
    for mc in (1, 2):
        q_ind = unreliability(navigation_model(mission_computers=mc), MISSION_HOURS)
        q_ccf = unreliability(physical_ccf_model(mission_computers=mc), MISSION_HOURS)
        nav.append([f"{mc} mission computer(s)", q_ind, q_ccf, q_ccf / q_ind])
    claimed = nav[0][1] / nav[1][1]
    real = nav[0][2] / nav[1][2]
    navigation = table(["variant", "independence", "physical CCF (table β)", "ratio"], nav)
    second_mc = table(
        ["quantity", "value"],
        [
            ["benefit of the 2nd mission computer, independence", claimed],
            ["benefit of the 2nd mission computer, physical CCF", real],
            [
                "orders of magnitude claimed, then kept (log10 of each benefit)",
                f"{math.log10(claimed):.2f} → {math.log10(real):.2f}",
            ],
        ],
    )

    dual = physical_ccf_model(mission_computers=2)
    q = dual.probabilities(MISSION_HOURS)
    total = unreliability(dual, MISSION_HOURS)
    cuts = sorted(minimal_cut_sets(dual, max_order=2), key=lambda c: -math.prod(q[e] for e in c))
    cut_table = table(
        ["minimal cut set (order ≤ 2)", "order", "probability (10 h)", "share"],
        [
            [
                " + ".join(sorted(c)),
                len(c),
                math.prod(q[e] for e in c),
                math.prod(q[e] for e in c) / total,
            ]
            for c in cuts[:8]
        ],
    )

    # Sweep: one beta applied to every redundant set of the dual-computer system.
    sweep_b = np.linspace(0.0, 0.1, 11)
    sweep = [
        unreliability(
            physical_ccf_model(
                mission_computers=2,
                betas=dict.fromkeys(
                    ("nav_source", "data_bus", "power", "mission_computer"), float(b)
                ),
            ),
            MISSION_HOURS,
        )
        for b in sweep_b
    ]
    sweep_table = table(
        ["β on every redundant set", "P(loss of navigation)", "vs independence"],
        [[float(b), s, s / sweep[0]] for b, s in zip(sweep_b, sweep, strict=True)],
    )

    plotting.use_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8))
    colors = [
        plotting.INDEPENDENT_COLOR,
        "#3a8f5c",
        plotting.PHYSICAL_COLOR,
        plotting.CYBER_COLOR,
        "#7a4fa3",
    ]
    for b, color in zip(BETAS, colors, strict=True):
        ax1.semilogy(MS, [grid[(b, m)] for m in MS], "o-", color=color, label=f"β = {b}")
        if b > 0:
            ax1.axhline(ccf_floor(RATE, b, MISSION_HOURS), color=color, ls=":", lw=1)
    ax1.set_xlabel("identical EGIs m (1-of-m)")
    ax1.set_ylabel("P(all fail in 10 h)")
    ax1.set_title("Identical redundancy hits the β floor (dotted)")
    ax1.legend(fontsize=8)
    ax2.semilogy(sweep_b, sweep, "o-", color=plotting.PHYSICAL_COLOR, label="physical CCF")
    ax2.axhline(sweep[0], color=plotting.INDEPENDENT_COLOR, ls="--", label="independence")
    ax2.set_xlabel("β on every redundant set")
    ax2.set_ylabel("P(loss of navigation in 10 h)")
    ax2.set_title("Navigation, two mission computers")
    ax2.legend(fontsize=8)
    for ax in (ax1,):
        ax.xaxis.get_major_locator().set_params(integer=True)
    fig.subplots_adjust(wspace=0.35)
    fig.savefig(FIGURES / "physical_ccf.png")
    plt.close(fig)

    write_result(
        "physical_ccf",
        "Phase 2: physical common-cause failure",
        [
            ("Beta factors (all assumptions)", params),
            ("One group of identical EGIs, 1-of-m: unreliability over 10 h", cap),
            ("What each extra identical unit buys", gain),
            ("Beta factor vs MGL for three EGIs (same β)", mgl),
            ("Navigation system: independence vs physical CCF", navigation),
            ("The second mission computer", second_mc),
            ("Two mission computers, physical CCF: leading cut sets", cut_table),
            ("Sensitivity: one β on every redundant set, two mission computers", sweep_table),
        ],
    )


if __name__ == "__main__":
    main()
