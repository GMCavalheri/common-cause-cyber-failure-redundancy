"""Phase 2: physical common-cause failure (beta factor, MGL and alpha factor).

Parametric models give the fractions of a component's failures that are shared by ``k``
members of its group; :func:`apply_ccf` turns a group into shared basic events of the Phase 1
engine, so the result is quantified exactly.
"""

from cyberccf.physical_ccf_beta_factor.closed_form import (
    beta_split,
    ccf_floor,
    one_of_m_beta_unreliability,
    two_of_three_rare_event,
)
from cyberccf.physical_ccf_beta_factor.groups import (
    CCFGroup,
    apply_ccf,
    apply_groups,
    beta_group,
    ccf_event_name,
)
from cyberccf.physical_ccf_beta_factor.navigation import (
    BetaRow,
    load_ccf_parameters,
    physical_ccf_model,
    physical_groups,
)
from cyberccf.physical_ccf_beta_factor.parametric import (
    alpha_fractions,
    alphas_from_fractions,
    beta_equivalent,
    beta_factor_fractions,
    check_fractions,
    independent_fractions,
    mgl_fractions,
)

__all__ = [
    "BetaRow",
    "CCFGroup",
    "alpha_fractions",
    "alphas_from_fractions",
    "apply_ccf",
    "apply_groups",
    "beta_equivalent",
    "beta_factor_fractions",
    "beta_group",
    "beta_split",
    "ccf_event_name",
    "ccf_floor",
    "check_fractions",
    "independent_fractions",
    "load_ccf_parameters",
    "mgl_fractions",
    "one_of_m_beta_unreliability",
    "physical_ccf_model",
    "physical_groups",
    "two_of_three_rare_event",
]
