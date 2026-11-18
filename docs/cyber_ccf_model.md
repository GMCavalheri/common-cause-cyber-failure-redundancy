# `cyber_ccf_model`: shared vulnerabilities and the cyber beta factor

**Lesson:** [3 · The cyber beta factor](lessons/03-the-cyber-beta-factor.md) ·
**Derivation:** [`derivation.md`](derivation.md) ·
**Code:** [`src/cyberccf/cyber_ccf_model/`](../src/cyberccf/cyber_ccf_model/)

## Model

Programmable channels carry attributes (firmware, network, supply chain). For each attribute
$d$ and value $v$ there is one event, at rate $\lambda_d = \nu_d p_d$ (attempts times success
probability), that fails every component holding $d = v$. The rate is per value, so a
component's cyber exposure $\lambda_c = \sum_d \lambda_d$ is the same in every architecture;
diversity changes only who shares it.

The cyber beta factor of a component is the share of its total rate from cyber events it
shares with another component. For identical channels
$\beta_c = \lambda_c/(\lambda_p + \lambda_c)$ and $1 - \beta = (1 - \beta_p)(1 - \beta_c)$.

## API

`Exposure`, `load_exposures`, `scaled`, `apply_cyber`, `cyber_beta`, `common_cause_share`,
`total_rate`, `navigation_attributes`, `cyber_ccf_model(..., distinct=..., shared_network=...,
exposure_scale=...)`, closed forms `combined_beta`, `cyber_beta_from_rates`,
`cyber_rate_from_beta`, `identical_group_unreliability`, `diverse_group_unreliability`,
`split_gain`.

## Assumptions

Effect level only (see [`scope.md`](scope.md)); rates are illustrative with no field data
([`cyber_exposures.csv`](../src/cyberccf/data/cyber_exposures.csv)); distinct values have
independent events; an event defeats every holder fully.

## Verification

Identical and diverse groups against closed forms; zero exposure equals the physical model;
identical navigation factors out every cyber event; more exposure never helps; refining an
attribute never hurts a redundant group (Hypothesis); and the exact split-gain identity.
