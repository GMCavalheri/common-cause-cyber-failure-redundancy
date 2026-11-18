"""Extra: what a declared NIST SP 800-82r3 posture says, and does not say, about cyber CCF."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from cyberccf import plotting
from cyberccf.case_study_application import REDUNDANT, REQUIREMENT, recommend
from cyberccf.cyber_ccf_model import DIMENSIONS
from cyberccf.security_posture import (
    LEVELS,
    controls_at,
    cyber_beta_range,
    decades,
    exposure_range,
    load_controls,
    load_rubric,
    unreliability_range,
)

from common import FIGURES, table, write_result


def main() -> None:
    rec = recommend()
    assert rec is not None
    diverse = rec.architecture

    controls = table(
        ["control", "title", "attribute", "low", "moderate", "high"],
        [
            [
                c.control,
                c.title,
                c.dimension,
                "x" if c.low else "",
                "x" if c.moderate else "",
                "x" if c.high else "",
            ]
            for c in load_controls()
        ],
    )
    r = load_rubric()
    rubric = table(
        ["parameter", "low", "high"],
        [
            ["fraction of remaining exposure removed by one control", r.effect_low, r.effect_high],
            ["exposure with no controls (× illustrative)", r.unprotected_low, r.unprotected_high],
        ],
    )
    counts = table(
        ["level", *[f"{d} controls" for d in DIMENSIONS]],
        [[lvl, *[len(controls_at(lvl, d)) for d in DIMENSIONS]] for lvl in LEVELS],
    )
    exposures = table(
        ["level", *[f"{d} (× illustrative)" for d in DIMENSIONS]],
        [
            [
                lvl,
                *[
                    f"{exposure_range(lvl)[d][0]:.3g} to {exposure_range(lvl)[d][1]:.3g}"
                    for d in DIMENSIONS
                ],
            ]
            for lvl in LEVELS
        ],
    )
    betas = table(
        ["level", "β_c of an EGI", "β_c of a mission computer"],
        [
            [
                lvl,
                "{:.3g} to {:.3g}".format(*cyber_beta_range(lvl, 2e-4)),
                "{:.3g} to {:.3g}".format(*cyber_beta_range(lvl, 5e-5)),
            ]
            for lvl in LEVELS
        ],
    )
    rows = []
    ranges = {}
    for lvl in LEVELS:
        ident = unreliability_range(REDUNDANT, lvl)
        div = unreliability_range(diverse, lvl)
        ranges[lvl] = (ident, div)
        rows.append(
            [
                lvl,
                f"{ident[0]:.3e} to {ident[1]:.3e}",
                f"{decades(*ident):.2f}",
                "yes" if ident[1] <= REQUIREMENT else "no",
                f"{div[0]:.3e} to {div[1]:.3e}",
                f"{decades(*div):.2f}",
                "yes" if div[1] <= REQUIREMENT else "no",
            ]
        )
    q_table = table(
        [
            "level",
            "identical design",
            "width (decades)",
            "meets 1e-4 at worst",
            "diverse design",
            "width (decades)",
            "meets 1e-4 at worst",
        ],
        rows,
    )

    plotting.use_style()
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    x = np.arange(len(LEVELS))
    for k, (label, color) in enumerate(
        [("redundant, identical", plotting.CYBER_COLOR), ("diverse (recommended)", "#3a8f5c")]
    ):
        lo = [ranges[lvl][k][0] for lvl in LEVELS]
        hi = [ranges[lvl][k][1] for lvl in LEVELS]
        ax.vlines(x + (k - 0.5) * 0.25, lo, hi, color=color, lw=8, label=label)
    ax.axhline(
        REQUIREMENT, color=plotting.NEUTRAL_COLOR, ls=":", lw=1, label="illustrative requirement"
    )
    ax.set_yscale("log")
    ax.set_xticks(x, [f"{lvl}" for lvl in LEVELS])
    ax.set_xlabel("NIST SP 800-82r3 OT overlay level implemented")
    ax.set_ylabel("P(loss of navigation in 10 h)")
    ax.set_title("What a declared posture allows: ranges, not points")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3)
    fig.savefig(FIGURES / "posture.png")
    plt.close(fig)

    write_result(
        "posture",
        "Extra: NIST SP 800-82r3 posture to a range of cyber exposure",
        [
            ("Overlay controls that act on the three attributes (SP 800-82r3 Table 22)", controls),
            ("Rubric parameters (illustrative assumptions)", rubric),
            ("Controls selected per level and attribute", counts),
            ("Exposure interval per level", exposures),
            ("Cyber beta factor interval per level", betas),
            ("P(loss of navigation) interval per level", q_table),
        ],
    )


if __name__ == "__main__":
    main()
