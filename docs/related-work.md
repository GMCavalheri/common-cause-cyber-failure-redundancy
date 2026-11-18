# Related work, and what is (and isn't) new

This note places the project among the work it builds on and states, as narrowly as the
evidence allows, what it adds. It is the first pass of the literature review the RES-03 paper
needs ("is there an existing quantitative model of cyber-induced common-cause failure?"). Every
source below was checked on the web on 2026-11-17; section 6 lists the searches and what is
still to be done before any novelty claim is published.

## 1. Classical common-cause failure

* **Beta factor.** K. N. Fleming, *A Reliability Model for Common Mode Failures in Redundant
  Safety Systems*, General Atomic GA-A13284, 1975. A fraction $\beta$ of a component's failures
  fails the whole redundant group. This project's Lesson 2 and Proposition 3 build on it.
* **Basic parameter, MGL and alpha-factor models.** A. Mosleh, D. M. Rasmuson and F. M.
  Marshall, *Guidelines on Modeling Common-Cause Failures in Probabilistic Risk Assessment*,
  NUREG/CR-5485, U.S. NRC, 1998. Defines the basic-event formulation (Section 5.3), the root
  cause and coupling factor vocabulary, the parametric models (Eqs. 5.5-5.11) and the
  quantification tables used as test oracles here (Tables 5-4 and 5-5); its companion
  NUREG/CR-6268 covers event data collection and classification.
* **The testing-scheme subtlety.** J. E. Stott, P. T. Britton, R. W. Ring, F. Hark and G. S.
  Hatfield, "Common Cause Failure Modeling: Aerospace vs. Nuclear," NASA NTRS 20100025991, 2010.
  Shows that staggered and non-staggered alpha-factor estimates differ and that nuclear generic
  factors do not transfer to aerospace without care.
* **Beta values for electronics.** IEC 61508-6 Annex D gives beta between 0.005 and 0.05 for
  programmable electronics and 0.01 and 0.1 for field equipment, as quoted by S. Gandy, "The
  importance of considering common cause with redundant systems," exida blog, 15 August 2023
  (the standard is paid and is not used directly).

**Relation to this project:** standard methodology, re-implemented and tested against the
published equations and tables. Nothing new.

## 2. Design diversity and coincident failures

* A. Avižienis, "The N-version approach to fault-tolerant software," *IEEE Trans. Software
  Engineering* SE-11(12), 1985. Diversity of implementation as a defence against common design
  faults.
* D. E. Eckhardt and L. D. Lee, "A theoretical basis for the analysis of multiversion software
  subject to coincident errors," *IEEE Trans. Software Engineering* SE-11(12), pp. 1511-1517,
  1985; and B.
  Littlewood and D. R. Miller, "Conceptual modeling of coincident failures in multiversion
  software," *IEEE Trans. Software Engineering* 15(12), pp. 1596-1614, 1989. Independently developed versions
  still fail together more often than independence predicts, because some inputs are hard for
  everyone; forced diversity can do better.
* J. C. Knight and N. G. Leveson, "An experimental evaluation of the assumption of independence
  in multiversion programming," *IEEE Trans. Software Engineering* SE-12(1), 1986. The
  experiment that rejected independence of separately developed versions.

**Relation:** this literature is about *accidental* faults and shows diversity is weaker than
independence. This project assumes that distinct attribute values carry *independent*
shared-vulnerability events (Proposition 4), which is the optimistic end of that literature.
For attacks the assumption is arguably more defensible (an exploit is specific to an
implementation), but it is an assumption, and a coincident-vulnerability model in the
Eckhardt-Lee sense would be the natural refinement.

## 3. Software common-cause failure in digital instrumentation and control

* T. Shorthill, H. Bao, E. Chen and H. Ban, "An Application of a Modified Beta Factor Method for
  the Analysis of Software Common Cause Failures," arXiv:2206.11321, 2022 (Idaho National
  Laboratory, DOE Light Water Reactor Sustainability program). Identifies **software-centric
  attributes of the coupling mechanism** and uses a modified beta factor that lets **one
  component belong to several common-cause component groups**, with software-specific
  parameters where operational data are missing.
* The same INL programme's integrated risk-assessment framework for digital I&C
  (arXiv:2112.09287) and its redundancy-guided hazard analysis for CCF.

**Relation:** this is the closest prior work found. Its structure, coupling attributes that
define overlapping groups, is the same as this project's attribute events (Lesson 3). The
differences: it addresses software *design faults* and does not mention cyber attack or
security; this project addresses shared *vulnerabilities* exercised by an attacker, with a rate
built from attempts and success probability, and a security-posture mapping. Any novelty claim
must be stated relative to this paper.

## 4. Diversity for security

* D. Geer, R. Bace, P. Gutmann, P. Metzger, C. P. Pfleeger, J. S. Quarterman and B. Schneier,
  *CyberInsecurity: The Cost of Monopoly*, Computer and Communications Industry Association,
  24 September 2003. The monoculture argument: one dominant platform is a common mode for a whole society's
  computers. Qualitative.
* B. Littlewood and L. Strigini, "Redundancy and diversity in security," *Computer Security,
  ESORICS 2004*, LNCS 3193, pp. 423-438. Carries probabilistic reasoning about redundancy,
  diversity and independence from reliability into security (layers of defence, intrusion
  detection). The closest conceptual ancestor of this project, at the level of principles.
* B. Cox, D. Evans, A. Filipi, J. Rowanhill, W. Hu, J. Davidson, J. Knight, A. Nguyen-Tuong and
  J. Hiser, "N-Variant Systems: A Secretless Framework for Security through Diversity," *15th
  USENIX Security Symposium*, 2006. Runs diversified variants so that one exploit cannot
  compromise all of them at once. A mechanism, not a reliability model.
* M. Zhang, L. Wang, S. Jajodia, A. Singhal and M. Albanese, "Network Diversity: A Security
  Metric for Evaluating the Resilience of Networks Against Zero-Day Attacks," *IEEE Trans.
  Information Forensics and Security* 11(5), 2016. Quantifies how much software diversity in a
  network raises the effort of zero-day attack paths.

**Relation:** these works establish that diversity is a security property and measure it in
attacker effort or in the existence of attack paths. None of them puts the effect into the
reliability engineer's quantities (beta factor, mission unreliability, availability, MTBF) or
compares it with physical common cause in one model.

## 5. Safety, security and their co-engineering

* S. Kriaa, L. Piètre-Cambacédès, M. Bouissou and Y. Halgand, "A survey of approaches combining
  safety and security for industrial control systems," *Reliability Engineering & System Safety*
  139, pp. 156-178,
  2015. Surveys joint safety-security methods (fault trees with attack trees, BDMP, STPA-Sec
  and others).
* CPS-02 of this portfolio (GMCavalheri/cyber-physical-rbd-attack-trees) unifies block diagrams
  and attack trees, and its Lesson 5 flags "two computers loaded from the same compromised
  laptop" as a common cause with $\beta = 1$; this project is the study that remark called for.
* K. Stouffer et al., *Guide to Operational Technology (OT) Security*, NIST SP 800-82 Rev. 3,
  2023, and NIST SP 800-53B, 2020. The OT overlay selects segmentation (SC-7(29) at every level)
  but the catalogue's heterogeneity control SC-29 is in no baseline (Lesson 7).

## 6. What is (and isn't) new

| claim | where | assessment |
|---|---|---|
| Shared cyber vulnerabilities are common-cause failures, with coupling factors firmware, network and supply chain | Lesson 3 | **Not new as an idea.** Implicit in the monoculture literature and in software-CCF work; stated explicitly here in NUREG/CR-5485 vocabulary. |
| Attribute-defined events with per-value rates, so a component's exposure is conserved and only its sharing depends on the architecture (Proposition 2) | derivation | **A modelling choice, close to Shorthill et al. (2022)** for software faults; new, as far as these searches show, for attacker-exercised vulnerabilities with a thinned-Poisson rate. |
| $1 - \beta = (1-\beta_p)(1-\beta_c)$ for identical channels, so every beta-factor formula applies with the effective $\beta$ (Proposition 3) | derivation | **Elementary** (superposition of Poisson processes) but, in these searches, not stated before for a cyber term; useful because it lets existing calculations absorb the correction. |
| The best gain of identical redundancy is $1/\beta$, now with the cyber term (Proposition 7) | derivation | **Classical for physical beta**; the cyber reading is the contribution. |
| Splitting a shared event lowers a redundant group's failure probability by exactly $k(1-k)P(\bar U \cap \bar V)$, so diversity never hurts a redundant group, and common cause can *help* a series group (Propositions 5, 6) | derivation | **Elementary probability**; the exact identity was not found stated in the CCF literature in these searches. It makes the plan's directionality check precise. |
| Quantified case study: on the navigation system, redundancy buys 2.74 orders as claimed, 1.60 with physical CCF, 0.88 with cyber CCF; diversity restores the physical figure and makes it insensitive to the exposure | Lessons 5-6 | **New as a worked example**, synthetic and illustrative; its value is the structure of the result, not the numbers. |
| The ranking of diversity investments does not depend on the overall exposure level; the exposure decides only diversity against more identical hardware | Lesson 4 | **New observation**, first-order argument; holds for this cost model. |
| A security posture maps to a *range* of exposure; posture moves it down but does not narrow it, and SC-29 is in no baseline | Lesson 7 | **New as a mapping**; the rubric's weights are assumptions. The SC-29 fact is from the NIST documents. |

**Honest summary.** The project is an application and modest extension of established CCF
methodology to a cause it was not built for. Its closest neighbour (Shorthill et al., 2022)
already uses coupling attributes and overlapping groups for software faults; its conceptual
ancestor (Littlewood & Strigini, 2004) already argued that reliability's probabilistic view of
diversity applies to security. What these searches did not find is a model that puts shared
*vulnerabilities* into the beta-factor calculation a reliability engineer already does, with a
closed-form combination with the physical beta, structural results about diversity, and a
quantified before-and-after on a redundant architecture. That is the claim, and it is narrow on
purpose.

### Searches done and still needed

Done (web search, 2026-11-17): "cyber attack induced common cause failure redundant channels
quantitative model beta factor PRA"; "common cause failure cyber redundant safety system nuclear
digital I&C"; "beta factor cybersecurity common cause failure safety instrumented system IEC
61511"; software CCF in digital I&C at INL; monoculture and diversity in security; network
diversity metrics; N-variant systems. None returned a quantitative cyber-CCF model.

Still needed before RES-03 states any novelty claim: a systematic search of *Reliability
Engineering & System Safety*, *IEEE Transactions on Reliability*, the PSAM and RAMS proceedings
and IEEE Xplore (terms: "cyber common cause", "security common cause failure", "cyber-induced
CCF", "attack common mode", "diversity security reliability model"), the NRC and EPRI digital
I&C reports (including the NEI 20-07 guidance on software CCF), and forward citations of
Shorthill et al. (2022) and Littlewood & Strigini (2004).
