import matplotlib.pyplot as plt

from cyberccf import plotting


def test_style_sets_shared_rcparams() -> None:
    plotting.use_style()
    assert plt.rcParams["savefig.bbox"] == "tight"
    assert plt.rcParams["axes.spines.top"] is False
    assert len(set(plotting.SERIES_COLORS)) == len(plotting.SERIES_COLORS)
