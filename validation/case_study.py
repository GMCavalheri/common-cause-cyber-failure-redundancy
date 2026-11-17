"""Phase 5: the case study. Redundancy as usually claimed vs redundancy as it is."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np

from cyberccf import plotting
from cyberccf.architecture_diversity_tradeoff import make_architecture
from cyberccf.case_study_application import (
    EXPOSURE_RANGE,
    REDUNDANT,
    REQUIREMENT,
    SINGLE_STRING,
    recommend,
    tornado,
    views,
)

from common import FIGURES, table, write_result


def main() -> None:
    rec = recommend()
    assert rec is not None
    designs = [
        ("single string (1 EGI, 1 bus channel, 1 computer)", views(SINGLE_STRING, bus_channels=1)),
        ("CPS-01/02 baseline (2 EGI, 2 bus channels, 1 computer)", views(make_architecture(2, 1))),
        ("redundant, identical (2 EGI, 2 bus channels, 2 computers)", views(REDUNDANT)),
        (f"recommended: {rec.architecture.label}", views(rec.architecture)),
    ]
    lo, hi = EXPOSURE_RANGE
    before_after = table(
        [
            "design",
            "as claimed (independence)",
            "physical CCF",
            "physical + cyber CCF",
            f"cyber range (× {lo:g} to × {hi:g})",
            "physical + cyber vs as claimed",
        ],
        [
            [
                name,
                v.as_claimed,
                v.physical,
                v.cyber,
                f"{v.cyber_low:.3e} to {v.cyber_high:.3e}",
                v.cyber / v.as_claimed,
            ]
            for name, v in designs
        ],
    )

    single, _, redundant, recommended = (v for _, v in designs)
    benefit_rows = []
    for label, a, b in [
        ("as claimed (independence)", single.as_claimed, redundant.as_claimed),
        ("physical CCF", single.physical, redundant.physical),
        ("physical + cyber CCF", single.cyber, redundant.cyber),
        (f"physical + cyber, exposure × {hi:g}", single.cyber_high, redundant.cyber_high),
    ]:
        benefit_rows.append([label, a / b, f"{math.log10(a / b):.2f}"])
    benefit = table(
        ["model", "benefit of redundancy (single string / redundant)", "orders of magnitude"],
        benefit_rows,
    )

    bars = tornado()
    tornado_table = table(
        ["parameter", "low", "high", "P(loss) at low", "P(loss) at high", "swing"],
        [[b.parameter, b.low_label, b.high_label, b.q_low, b.q_high, b.swing] for b in bars],
    )

    recommendation = table(
        ["quantity", "value"],
        [
            ["illustrative requirement, P(loss of navigation) per 10 h mission", REQUIREMENT],
            [
                "worst case considered",
                f"cyber exposure × {hi:g} (P(loss) never falls with exposure)",
            ],
            ["cheapest design meeting it (of 315)", rec.architecture.label],
            ["relative cost (illustrative)", rec.cost],
            ["P(loss) at the illustrative exposure", rec.q_illustrative],
            ["P(loss) at the worst case", rec.q_worst],
            ["redundant identical design at the worst case", redundant.cyber_high],
            ["redundant identical design, as claimed", redundant.as_claimed],
        ],
    )

    plotting.use_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.1, 1]})
    names = [
        "single\nstring",
        "CPS-01/02\nbaseline",
        "redundant\n(identical)",
        "diverse\n(recom-\nmended)",
    ]
    x = np.arange(len(designs))
    w = 0.26
    for k, (attr, label, color) in enumerate(
        [
            ("as_claimed", "as claimed (independence)", plotting.INDEPENDENT_COLOR),
            ("physical", "physical CCF", plotting.PHYSICAL_COLOR),
            ("cyber", "physical + cyber CCF", plotting.CYBER_COLOR),
        ]
    ):
        vals = [getattr(v, attr) for _, v in designs]
        ax1.bar(x + (k - 1) * w, vals, w, color=color, label=label)
    lows = [v.cyber_low for _, v in designs]
    highs = [v.cyber_high for _, v in designs]
    mids = [v.cyber for _, v in designs]
    ax1.errorbar(
        x + w,
        mids,
        yerr=[np.subtract(mids, lows), np.subtract(highs, mids)],
        fmt="none",
        ecolor="black",
        capsize=3,
        lw=1,
    )
    ax1.axhline(
        REQUIREMENT, color=plotting.NEUTRAL_COLOR, ls=":", lw=1, label="illustrative requirement"
    )
    ax1.set_yscale("log")
    ax1.set_xticks(x, names, fontsize=8)
    ax1.set_ylabel("P(loss of navigation in 10 h)")
    ax1.set_title(f"Before and after (bars: × {lo:g} to × {hi:g} exposure)")
    ax1.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=2)
    base = views(REDUNDANT).cyber
    y = np.arange(len(bars))[::-1]
    for yi, b in zip(y, bars, strict=True):
        ax2.barh(yi, b.q_high - base, left=base, color=plotting.CYBER_COLOR, height=0.6)
        ax2.barh(yi, b.q_low - base, left=base, color=plotting.INDEPENDENT_COLOR, height=0.6)
    ax2.axvline(base, color="black", lw=1)
    ax2.set_yticks(y, [b.parameter for b in bars], fontsize=8)
    ax2.set_xlabel("P(loss of navigation in 10 h), × 10⁻³")
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v * 1e3:g}"))
    ax2.set_title("Tornado, redundant identical design\n(blue: low value, red: high value)")
    fig.subplots_adjust(wspace=0.55)
    fig.savefig(FIGURES / "case_study.png")
    plt.close(fig)

    write_result(
        "case_study",
        "Phase 5: case study, redundancy as claimed vs as it is",
        [
            ("Before and after: P(loss of trusted navigation) per 10 h mission", before_after),
            ("What redundancy buys under each model", benefit),
            ("Tornado: redundant identical design", tornado_table),
            ("A recommendation that holds across the exposure range", recommendation),
        ],
    )


if __name__ == "__main__":
    main()
