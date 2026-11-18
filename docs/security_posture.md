# `security_posture`: a NIST SP 800-82r3 posture as a range of exposure

**Lesson:** [7 · From a security posture to a number](lessons/07-from-a-security-posture-to-a-number.md) ·
**Code:** [`src/cyberccf/security_posture/`](../src/cyberccf/security_posture/)

## Model

[`nist_overlay_controls.csv`](../src/cyberccf/data/nist_overlay_controls.csv) transcribes, from
NIST SP 800-82 Rev. 3 Appendix F (Table 22), the OT-overlay controls that act on each attribute
and the levels that select them. The rubric
([`posture_rubric.csv`](../src/cyberccf/data/posture_rubric.csv), illustrative): with no
controls the exposure is 0.25 to 10 times the illustrative rates, and each selected control
removes 5 % to 25 % of the remaining exposure of its attribute. A level maps to an interval of
exposure per attribute (`exposure_range`), of cyber beta (`cyber_beta_range`) and of P(loss)
(`unreliability_range`, the two corners, since unreliability is monotone in every exposure).

SC-29 Heterogeneity is listed with no level: it is in no NIST SP 800-53B baseline (Table 3-18)
and absent from the overlay.

## Verification

Spot checks of the transcription; nested levels; valid ranges; a stronger posture never raises
either end of any interval; the corners equal rebuilt models.
