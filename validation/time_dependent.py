"""Extra: availability and MTBF with repair, and the Monte Carlo checks of every exact engine."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from cyberccf import plotting
from cyberccf.architecture_diversity_tradeoff import make_architecture
from cyberccf.case_study_application import REDUNDANT, recommend
from cyberccf.cyber_ccf_model import cyber_ccf_model
from cyberccf.independence_baseline import (
    MISSION_HOURS,
    Model,
    component_specs,
    navigation_model,
    unreliability,
)
from cyberccf.physical_ccf_beta_factor import physical_ccf_model
from cyberccf.time_dependent import (
    simulate_availability,
    simulate_missions,
    steady_state,
    transient_unreliability,
)

from common import FIGURES, table, write_result

SEED = 20261117


def mttr(n_egi: int, n_mc: int) -> dict[str, float]:
    return {n: s.mttr_hours for n, s in component_specs(n_egi, 2, mission_computers=n_mc).items()}


def ci(est: object) -> str:
    """``value [low, high]`` with three significant digits."""
    return f"{est.value:.3e} [{est.low:.3e}, {est.high:.3e}]"  # type: ignore[attr-defined]


def accelerated(model: Model, factor: float) -> Model:
    """The same model with every rate multiplied (so a short simulation sees many events)."""
    from dataclasses import replace

    return Model(
        model.name,
        model.structure,
        tuple(replace(e, rate_per_hour=e.rate_per_hour * factor) for e in model.events),
        model.causes,
    )


def main() -> None:
    rec = recommend()
    assert rec is not None
    designs = [
        ("CPS-01/02 baseline (2 EGI, 1 computer)", make_architecture(2, 1)),
        ("redundant identical (2 EGI, 2 computers)", REDUNDANT),
        ("diverse (recommended)", rec.architecture),
    ]
    rows = []
    mtbf_plot = []
    for label, arch in designs:
        times = mttr(arch.egi_units, arch.mission_computers)
        models = {
            "as claimed": navigation_model(mission_computers=arch.mission_computers),
            "physical CCF": physical_ccf_model(2, 2, arch.mission_computers),
            "physical + cyber CCF": arch.model(),
        }
        mt = []
        for view, model in models.items():
            ss = steady_state(model, times)
            rows.append([label, view, f"{ss.availability:.7f}", ss.unavailability, ss.mtbf, ss.mdt])
            mt.append(ss.mtbf)
        mtbf_plot.append(mt)
    steady = table(
        ["design", "view", "availability", "unavailability", "MTBF (h)", "MDT (h)"], rows
    )

    # Monte Carlo checks.
    rng = np.random.default_rng(SEED)
    checks = []
    for label, model, hours in [
        ("identical, 2 computers, 10 h", cyber_ccf_model(mission_computers=2), MISSION_HOURS),
        (
            "identical, one shared segment, 2 000 h",
            cyber_ccf_model(mission_computers=2, shared_network=True),
            2000.0,
        ),
        ("diverse (recommended), 2 000 h", rec.architecture.model(), 2000.0),
    ]:
        exact = unreliability(model, hours)
        markov = transient_unreliability(model, hours)
        est = simulate_missions(model, hours, 2_000_000, rng)
        checks.append(
            [
                f"missions: {label}",
                exact,
                f"{markov:.4e}",
                ci(est),
                "yes" if est.covers(exact) else "NO",
            ]
        )
    factor = 100.0
    for label, arch in designs[1:]:
        model = accelerated(arch.model(), factor)
        times = mttr(arch.egi_units, arch.mission_computers)
        exact = steady_state(model, times)
        sim = simulate_availability(model, times, 20_000.0, 20, rng)
        checks.append(
            [
                f"unavailability, rates × {factor:g}: {label}",
                exact.unavailability,
                "—",
                ci(sim.unavailability),
                "yes" if sim.unavailability.covers(exact.unavailability) else "NO",
            ]
        )
        checks.append(
            [
                f"failure frequency, rates × {factor:g}: {label}",
                exact.failure_frequency,
                "—",
                ci(sim.failure_frequency),
                "yes" if sim.failure_frequency.covers(exact.failure_frequency) else "NO",
            ]
        )
    mc = table(
        [
            "quantity",
            "exact (BDD or Markov)",
            "Markov e^(Gt)",
            "Monte Carlo [99.7 % interval]",
            "covers",
        ],
        checks,
    )

    plotting.use_style()
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    x = np.arange(len(designs))
    w = 0.26
    for k, (view, color) in enumerate(
        zip(
            ["as claimed", "physical CCF", "physical + cyber CCF"],
            [plotting.INDEPENDENT_COLOR, plotting.PHYSICAL_COLOR, plotting.CYBER_COLOR],
            strict=True,
        )
    ):
        ax.bar(x + (k - 1) * w, [m[k] for m in mtbf_plot], w, color=color, label=view)
    ax.set_yscale("log")
    ax.set_xticks(
        x,
        ["CPS-01/02 baseline\n(1 computer)", "redundant\nidentical", "diverse\n(recommended)"],
        fontsize=8,
    )
    ax.set_ylabel("system MTBF (hours, with repair)")
    ax.set_title("Mean time between losses of trusted navigation")
    ax.legend(fontsize=8)
    fig.savefig(FIGURES / "time_dependent.png")
    plt.close(fig)

    write_result(
        "time_dependent",
        "Extra: availability and MTBF with repair, and Monte Carlo checks",
        [
            ("Steady state with repair (exponential repair, each component its own clock)", steady),
            ("Monte Carlo checks of the exact engines (seeded)", mc),
        ],
    )


if __name__ == "__main__":
    main()
