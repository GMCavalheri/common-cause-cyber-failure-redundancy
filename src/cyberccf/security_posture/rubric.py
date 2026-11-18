"""From a declared security posture to a *range* of cyber exposure and cyber beta factor.

The NIST SP 800-82 Rev. 3 OT overlay (Appendix F, Table 22) lists which NIST SP 800-53 Rev. 5
controls an OT system should implement at the low, moderate and high impact levels.
``data/nist_overlay_controls.csv`` keeps the controls that act on the three attributes of this
project: boundary protection and segmentation for the **network**, least functionality, flaw
remediation and software/firmware integrity for the **firmware**, and supply-chain risk
management for the **supply chain**. Every row is transcribed from that table.

The rubric (``data/posture_rubric.csv``, every number an illustrative assumption) says:

* with no overlay control, the exposure is anywhere in ``unprotected_scale`` times the
  illustrative rates (the project-wide range);
* each selected control removes a fraction ``f`` in ``control_effect`` of the remaining
  exposure of its attribute, so ``n`` controls multiply it by ``(1 - f)**n``.

A posture level therefore maps to an interval of exposure multipliers per attribute, and,
because unreliability is non-decreasing in every exposure (tested), to an interval of
unreliability whose ends are the two corner cases. The output is always a range, never a
point: the rubric turns a declared posture into a statement a reliability engineer can use,
without pretending to a precision nobody has.

One row is listed for what it shows: **SC-29 Heterogeneity**, the catalogue's diversity
control, is selected in no NIST SP 800-53B baseline and does not appear in the overlay. So no
posture level changes *which* channels share an exposure; posture lowers the exposure, and only
design diversity removes the sharing.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from importlib import resources

from cyberccf.architecture_diversity_tradeoff.architectures import Architecture
from cyberccf.case_study_application.case_study import unreliability_with
from cyberccf.cyber_ccf_model.shared_vulnerability import DIMENSIONS, load_exposures
from cyberccf.independence_baseline.model import BasicEvent
from cyberccf.independence_baseline.navigation import MISSION_HOURS

LEVELS = ("none", "low", "moderate", "high")


@dataclass(frozen=True)
class OverlayControl:
    """One control of the OT overlay and the levels that select it."""

    control: str
    title: str
    dimension: str
    low: bool
    moderate: bool
    high: bool
    source: str

    def selected(self, level: str) -> bool:
        """Is the control selected at ``level``?"""
        if level not in LEVELS:
            raise ValueError(f"level must be one of {LEVELS}")
        return level != "none" and bool(getattr(self, level))


def load_controls() -> list[OverlayControl]:
    """The overlay controls of ``nist_overlay_controls.csv``."""
    text = resources.files("cyberccf.data").joinpath("nist_overlay_controls.csv").read_text()
    return [
        OverlayControl(
            r["control"],
            r["title"],
            r["dimension"],
            r["low"] == "1",
            r["moderate"] == "1",
            r["high"] == "1",
            r["source"],
        )
        for r in csv.DictReader(text.splitlines())
    ]


@dataclass(frozen=True)
class Rubric:
    """The two illustrative parameter ranges of the rubric."""

    effect_low: float
    effect_high: float
    unprotected_low: float
    unprotected_high: float


def load_rubric() -> Rubric:
    """``posture_rubric.csv``."""
    text = resources.files("cyberccf.data").joinpath("posture_rubric.csv").read_text()
    rows = {r["parameter"]: r for r in csv.DictReader(text.splitlines())}
    return Rubric(
        float(rows["control_effect"]["low"]),
        float(rows["control_effect"]["high"]),
        float(rows["unprotected_scale"]["low"]),
        float(rows["unprotected_scale"]["high"]),
    )


def controls_at(level: str, dimension: str) -> list[OverlayControl]:
    """The controls protecting ``dimension`` that ``level`` selects."""
    return [c for c in load_controls() if c.dimension == dimension and c.selected(level)]


def exposure_range(level: str, rubric: Rubric | None = None) -> dict[str, tuple[float, float]]:
    """Per attribute, the interval of exposure multipliers (relative to the illustrative rates)."""
    r = rubric or load_rubric()
    out = {}
    for d in DIMENSIONS:
        n = len(controls_at(level, d))
        out[d] = (
            r.unprotected_low * (1 - r.effect_high) ** n,
            r.unprotected_high * (1 - r.effect_low) ** n,
        )
    return out


def cyber_beta_range(level: str, physical_rate: float) -> tuple[float, float]:
    """Interval of the cyber beta factor of an identical channel with this physical rate."""
    exp = load_exposures()
    rng = exposure_range(level)
    lo = sum(exp[d].rate_per_hour * rng[d][0] for d in DIMENSIONS)
    hi = sum(exp[d].rate_per_hour * rng[d][1] for d in DIMENSIONS)
    return lo / (physical_rate + lo), hi / (physical_rate + hi)


def unreliability_range(
    arch: Architecture, level: str, hours: float = MISSION_HOURS
) -> tuple[float, float]:
    """P(loss of navigation) at the two corners of the posture's exposure box."""
    model = arch.model()
    rng = exposure_range(level)

    def corner(k: int) -> float:
        def factor(e: BasicEvent) -> float:
            if not e.name.startswith("cyber:"):
                return 1.0
            return rng[e.name.split(":")[1].split("=")[0]][k]

        return unreliability_with(model, hours, factor)

    return corner(0), corner(1)


def decades(lo: float, hi: float) -> float:
    """Width of an interval in orders of magnitude."""
    return math.log10(hi / lo)
