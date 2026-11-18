# `physical_ccf_beta_factor`: beta factor, MGL and alpha factor

**Lesson:** [2 · When one cause breaks two channels](lessons/02-when-one-cause-breaks-two-channels.md) ·
**Code:** [`src/cyberccf/physical_ccf_beta_factor/`](../src/cyberccf/physical_ccf_beta_factor/)

## Model

A common-cause component group of $m$ identical members, each with total rate $\lambda$, is
described by fractions $f_k = Q_k/Q_t$ with $\sum_k \binom{m-1}{k-1} f_k = 1$ (NUREG/CR-5485):

* beta factor: $f_1 = 1 - \beta$, $f_m = \beta$;
* MGL: $f_k = \binom{m-1}{k-1}^{-1} \left(\prod_{i \le k} \rho_i\right)(1 - \rho_{k+1})$;
* alpha factor: $f_k = \alpha_k/\binom{m-1}{k-1}$ (staggered) or
  $k\alpha_k/(\binom{m-1}{k-1}\alpha_t)$ (non-staggered).

`apply_ccf` splits each member's own event to rate $f_1\lambda$ and adds one shared event of
rate $f_k\lambda$ per subset of size $k \ge 2$. Each member's total failure probability is
unchanged.

## API

`beta_factor_fractions`, `mgl_fractions`, `alpha_fractions`, `alphas_from_fractions`,
`check_fractions`, `CCFGroup`, `beta_group`, `apply_ccf`, `apply_groups`,
`physical_ccf_model`, `one_of_m_beta_unreliability`, `ccf_floor`, `two_of_three_rare_event`.

## Assumptions

Identical members (the parametric models assume symmetry). Beta values
([`ccf_parameters.csv`](../src/cyberccf/data/ccf_parameters.csv)) are assumptions inside the
IEC 61508-6 Annex D ranges, quoted from a free secondary source.

## Verification

NUREG/CR-5485 Eqs. 5.5-5.11 and every applicable row of Tables 5-4 and 5-5; conservation and
round trips (Hypothesis); unchanged marginals; the 1-of-m closed form and its floor; the
navigation system against a hand-derived form; and directionality: CCF never improves a
redundant group, although it can improve a series group.
