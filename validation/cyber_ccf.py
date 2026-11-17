"""Phase 3: what shared cyber vulnerabilities do to redundancy that physical CCF already dented."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np

from cyberccf import plotting
from cyberccf.cyber_ccf_model import (
    DIMENSIONS,
    Exposure,
    combined_beta,
    common_cause_share,
    cyber_beta,
    cyber_ccf_model,
    diverse_group_unreliability,
    identical_group_unreliability,
    load_exposures,
    navigation_attributes,
)
from cyberccf.independence_baseline import (
    MISSION_HOURS,
    minimal_cut_sets,
    navigation_model,
    unreliability,
)
from cyberccf.physical_ccf_beta_factor import (
    load_ccf_parameters,
    one_of_m_beta_unreliability,
    physical_ccf_model,
)

from common import FIGURES, table, write_result

LP = 2e-4  # EGI physical rate (assumption, CPS-01/02)
FULL = {(g, d): 2 for g in ("nav_source", "mission_computer") for d in DIMENSIONS}


def main() -> None:
    exp = load_exposures()
    lc = sum(e.rate_per_hour for e in exp.values())
    exposures = table(
        ["attribute", "attempts per hour", "P(defeats the channels)", "effective rate", "basis"],
        [
            [e.dimension, e.attempt_rate_per_hour, e.success_probability, e.rate_per_hour, e.basis]
            for e in exp.values()
        ],
    )

    beta_p = load_ccf_parameters()["nav_source"].beta
    net = exp["network"]
    doubled_network = exp | {
        "network": Exposure(net.dimension, 2 * net.attempt_rate_per_hour, net.success_probability)
    }
    dual = cyber_ccf_model(mission_computers=2)
    betas = table(
        [
            "component",
            "physical rate",
            "cyber exposure",
            "β_p",
            "β_c",
            "effective β (shared share)",
            "1 − (1 − β_p)(1 − β_c)",
        ],
        [
            [
                c,
                rate,
                lc,
                bp,
                cyber_beta(dual, c),
                common_cause_share(dual, c),
                combined_beta(bp, cyber_beta(dual, c)),
            ]
            for c, rate, bp in [
                ("egi_1", LP, beta_p),
                ("mission_computer_1", 5e-5, load_ccf_parameters()["mission_computer"].beta),
            ]
        ],
    )

    ms = [1, 2, 3, 4]
    rows = []
    for m in ms:
        rows.append(
            [
                m,
                one_of_m_beta_unreliability(m, LP, 0.0, MISSION_HOURS),
                one_of_m_beta_unreliability(m, LP, beta_p, MISSION_HOURS),
                identical_group_unreliability(m, LP, beta_p, lc, MISSION_HOURS),
                diverse_group_unreliability(m, LP, beta_p, lc, MISSION_HOURS),
            ]
        )
    group_table = table(
        [
            "EGIs (1-of-m)",
            "independence",
            "physical CCF",
            "+ cyber, identical",
            "+ cyber, fully diverse",
        ],
        rows,
    )

    variants = [
        ("independence (as usually claimed)", navigation_model(mission_computers=2)),
        ("physical CCF", physical_ccf_model(mission_computers=2)),
        ("physical + cyber CCF, identical channels", dual),
        (
            "... and one network segment for EGIs and computers",
            cyber_ccf_model(mission_computers=2, shared_network=True),
        ),
        (
            "... one segment, its exposure doubled for twice the attack surface",
            cyber_ccf_model(mission_computers=2, shared_network=True, exposures=doubled_network),
        ),
        (
            "... with fully diverse EGIs and computers",
            cyber_ccf_model(mission_computers=2, distinct=FULL),
        ),
    ]
    base = unreliability(variants[0][1], MISSION_HOURS)
    nav = table(
        ["two mission computers", "P(loss of navigation, 10 h)", "vs independence"],
        [
            [label, unreliability(m, MISSION_HOURS), unreliability(m, MISSION_HOURS) / base]
            for label, m in variants
        ],
    )

    single_rows = []
    for label, kwargs in [
        ("independence", None),
        ("physical CCF", {}),
        ("physical + cyber, identical", {"cyber": True}),
    ]:
        if kwargs is None:
            m1, m2 = navigation_model(), navigation_model(mission_computers=2)
        elif "cyber" in kwargs:
            m1, m2 = cyber_ccf_model(), cyber_ccf_model(mission_computers=2)
        else:
            m1, m2 = physical_ccf_model(), physical_ccf_model(mission_computers=2)
        q1, q2 = unreliability(m1, MISSION_HOURS), unreliability(m2, MISSION_HOURS)
        single_rows.append([label, q1, q2, q1 / q2, f"{math.log10(q1 / q2):.2f}"])
    second = table(
        ["model", "one computer", "two computers", "benefit of the 2nd", "orders of magnitude"],
        single_rows,
    )

    q = dual.probabilities(MISSION_HOURS)
    total = unreliability(dual, MISSION_HOURS)
    cuts = sorted(minimal_cut_sets(dual, max_order=2), key=lambda c: -math.prod(q[e] for e in c))
    cut_table = table(
        ["minimal cut set (order ≤ 2)", "kind", "probability (10 h)", "share"],
        [
            [
                " + ".join(sorted(c)),
                ", ".join(sorted({dual.event(e).kind for e in c})),
                math.prod(q[e] for e in c),
                math.prod(q[e] for e in c) / total,
            ]
            for c in cuts[:8]
        ],
    )
    by_kind: dict[str, float] = {}
    for c in cuts:
        if len(c) == 1:
            kind = dual.event(next(iter(c))).kind
            by_kind[kind] = by_kind.get(kind, 0.0) + q[next(iter(c))]
    kinds = table(
        ["order-one cut sets by origin", "probability (10 h)", "share of total"],
        [[k, v, v / total] for k, v in sorted(by_kind.items())],
    )

    scales = np.array([0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 10.0])
    sweep = []
    for s in scales:
        ident = cyber_ccf_model(mission_computers=2, exposure_scale=float(s))
        div = cyber_ccf_model(mission_computers=2, exposure_scale=float(s), distinct=FULL)
        sweep.append(
            [
                float(s),
                cyber_beta(ident, "egi_1"),
                unreliability(ident, MISSION_HOURS),
                unreliability(div, MISSION_HOURS),
                unreliability(ident, MISSION_HOURS) / unreliability(div, MISSION_HOURS),
            ]
        )
    sweep_table = table(
        [
            "exposure scale",
            "β_c of an EGI",
            "identical channels",
            "fully diverse",
            "identical / diverse",
        ],
        sweep,
    )
    attrs = navigation_attributes(mission_computers=2)
    attr_table = table(
        ["component", *DIMENSIONS],
        [[c, *[a[d] for d in DIMENSIONS]] for c, a in attrs.items()],
    )

    plotting.use_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8))
    labels = ["independence", "physical CCF", "+ cyber, identical", "+ cyber, fully diverse"]
    colors = [plotting.INDEPENDENT_COLOR, plotting.PHYSICAL_COLOR, plotting.CYBER_COLOR, "#3a8f5c"]
    styles = ["o-", "o-", "o-", "s--"]
    for j, (label, color, style) in enumerate(zip(labels, colors, styles, strict=True)):
        ax1.semilogy(ms, [r[j + 1] for r in rows], style, color=color, label=label)
    ax1.set_xlabel("EGIs m (1-of-m)")
    ax1.set_ylabel("P(all fail in 10 h)")
    ax1.set_title("One EGI group")
    ax1.xaxis.get_major_locator().set_params(integer=True)
    ax1.legend(fontsize=8)
    ax2.semilogy(
        scales, [r[2] for r in sweep], "o-", color=plotting.CYBER_COLOR, label="identical channels"
    )
    ax2.semilogy(scales, [r[3] for r in sweep], "s--", color="#3a8f5c", label="fully diverse")
    ax2.axhline(
        unreliability(variants[1][1], MISSION_HOURS),
        color=plotting.PHYSICAL_COLOR,
        ls=":",
        label="physical CCF only",
    )
    ax2.axhline(base, color=plotting.INDEPENDENT_COLOR, ls="--", label="independence")
    ax2.set_xlabel("cyber exposure (× the illustrative rates)")
    ax2.set_ylabel("P(loss of navigation in 10 h)")
    ax2.set_title("Navigation, two mission computers")
    ax2.legend(fontsize=8)
    fig.subplots_adjust(wspace=0.35)
    fig.savefig(FIGURES / "cyber_ccf.png")
    plt.close(fig)

    write_result(
        "cyber_ccf",
        "Phase 3: cyber common-cause failure",
        [
            ("Cyber exposures (illustrative assumptions, no field data)", exposures),
            ("Attributes of the programmable channels (baseline: identical)", attr_table),
            ("Cyber beta factors at the illustrative exposure", betas),
            ("One group of EGIs", group_table),
            ("Navigation system, two mission computers", nav),
            ("The second mission computer under each model", second),
            ("Physical + cyber, identical channels: leading cut sets", cut_table),
            ("Where the order-one cut sets come from", kinds),
            ("Sensitivity to the cyber exposure, two mission computers", sweep_table),
        ],
    )


if __name__ == "__main__":
    main()
