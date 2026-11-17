"""Phase 3: shared cyber vulnerabilities as common-cause failures.

Channel attributes (firmware, network segment, supply-chain source) define shared-vulnerability
events; the cyber beta factor is the share of a channel's failure rate they carry, and it
combines with the physical beta factor as ``1 - beta = (1 - beta_p)(1 - beta_c)``.
"""

from cyberccf.cyber_ccf_model.closed_form import (
    combined_beta,
    cyber_beta_from_rates,
    cyber_rate_from_beta,
    diverse_group_unreliability,
    identical_group_unreliability,
    split_gain,
)
from cyberccf.cyber_ccf_model.navigation import (
    PROGRAMMABLE,
    cyber_ccf_model,
    load_attribute_table,
    navigation_attributes,
)
from cyberccf.cyber_ccf_model.shared_vulnerability import (
    DIMENSIONS,
    Exposure,
    apply_cyber,
    common_cause_share,
    cyber_beta,
    cyber_event_name,
    load_exposures,
    scaled,
    total_rate,
)

__all__ = [
    "DIMENSIONS",
    "PROGRAMMABLE",
    "Exposure",
    "apply_cyber",
    "combined_beta",
    "common_cause_share",
    "cyber_beta",
    "cyber_beta_from_rates",
    "cyber_ccf_model",
    "cyber_event_name",
    "cyber_rate_from_beta",
    "diverse_group_unreliability",
    "identical_group_unreliability",
    "load_attribute_table",
    "load_exposures",
    "navigation_attributes",
    "scaled",
    "split_gain",
    "total_rate",
]
