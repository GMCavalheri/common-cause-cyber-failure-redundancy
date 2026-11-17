"""Matplotlib style shared by every figure in the repository (same as CPS-01/02/03)."""

from __future__ import annotations

import matplotlib.pyplot as plt

INDEPENDENT_COLOR = "#2f6db5"
"""Redundancy as usually claimed: independent channels."""
PHYSICAL_COLOR = "#e08a1e"
"""With physical common cause (the classical correction)."""
CYBER_COLOR = "#c8452c"
"""With physical and cyber common cause (this project's correction)."""
NEUTRAL_COLOR = "#555555"
SERIES_COLORS = (INDEPENDENT_COLOR, PHYSICAL_COLOR, CYBER_COLOR, "#3a8f5c", "#7a4fa3")


def use_style() -> None:
    """A clean, consistent style for every figure in the repository."""
    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "font.size": 10,
        }
    )
