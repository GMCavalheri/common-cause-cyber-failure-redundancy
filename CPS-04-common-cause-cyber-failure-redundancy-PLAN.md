# PLAN.md — CPS-04: Common-Cause Cyber Failure Analysis for Redundant Architectures

## Overview
A reliability engineering project addressing a subtle but critical gap in how redundancy is normally analyzed: classical reliability engineering treats redundant components (dual/triple redundant sensors or control channels) as statistically independent, which is a reasonable assumption for random physical failure but a dangerously wrong assumption when a shared cyber vulnerability can defeat all redundant channels simultaneously.

## Objective
Build an analysis framework that extends classical common-cause failure (CCF) modeling — already a recognized concept in reliability engineering for shared physical causes (e.g., a single power supply feeding "redundant" channels) — to explicitly include shared cyber vulnerabilities as a common-cause failure source, and quantify how much redundancy's reliability benefit is eroded when this is properly accounted for.

## Why This Project
This is arguably the single most important conceptual correction a reliability engineer can bring to a cyber-physical system: redundancy is the reliability engineer's most trusted tool, but if all three "redundant" channels run the same firmware with the same vulnerability, or share the same network segment, they are not independent — they can fail together under a single cyber attack, exactly the way common-cause failure already breaks the independence assumption for physical causes like a shared power bus. Most redundancy design in practice is still evaluated using physical CCF models only; explicitly modeling cyber CCF is a genuinely underexplored, high-value technical contribution.

## Knowledge Covered
1. **Classical Redundancy and Independence Baseline**: implement standard series/parallel reliability calculations assuming full independence between redundant channels, establishing the (overly optimistic) baseline reliability figure.
2. **Physical Common-Cause Failure Model**: implement the classical beta-factor CCF model for physical shared causes (e.g., shared power supply, shared environmental exposure), showing how it already reduces the naive independence estimate — this reproduces established, standard reliability engineering practice.
3. **Cyber Common-Cause Failure Model**: extend the beta-factor-style approach to a cyber CCF factor, representing the probability that a single cyber attack (exploiting a shared vulnerability across "redundant" channels — identical firmware, shared network segment, shared supply-chain component) defeats all redundant channels simultaneously.
4. **Architecture Diversity Trade-off Analysis**: model and compare different redundancy architecture choices — identical redundant channels (cheap, but higher cyber CCF risk) vs. diverse redundant channels (different vendors/firmware/network paths, more expensive, but structurally lower cyber CCF risk) — quantifying the reliability-vs-cost trade-off of diversity as a cyber risk mitigation, not just a classical physical-reliability design choice.
5. **Case Study Application**: apply the framework to the synthetic avionics/control architecture already used across the cyber-physical project series (reusing the system model from Cyber Attack Impact Modeling), producing a concrete before/after comparison of "redundancy as usually claimed" vs. "redundancy properly accounting for cyber CCF."

## Prerequisites / Background
- Basic redundancy/reliability concepts (series/parallel systems, as used in the Avionics Electronics Reliability RBD work)
- Classical Common-Cause Failure modeling concepts (e.g., the beta-factor model, a standard simplified CCF approach in reliability engineering)
- Basic understanding of shared-vulnerability concepts (same firmware/software stack, same network segment, same supply chain component across "redundant" channels)

## Data / Dataset
- **Synthetic architecture**: the shared avionics/control system model from CPS-01, with dual/triple redundant channels.
- **Common-cause failure methodology**: public references on beta-factor and related CCF parameter estimation (e.g., U.S. NRC NUREG/CR-5485 and standard reliability textbooks) for the physical CCF baseline and its worked examples.
- **Parameters**: illustrative physical failure rates and cyber common-cause probabilities, clearly labeled as assumptions and explored through sensitivity analysis.

## Tech Stack
- Python, NumPy
- Reuses the RBD/system model components from the Avionics Electronics Reliability and Cyber Attack Impact Modeling projects
- Matplotlib/Plotly for reliability-vs-diversity trade-off curves, before/after CCF comparison charts

## Repository Structure
```
common-cause-cyber-failure-redundancy/
  src/
    independence_baseline/
    physical_ccf_beta_factor/
    cyber_ccf_model/
    architecture_diversity_tradeoff/
    case_study_application/
  external/                # reused RBD/system model from prior projects
  docs/
  notebooks/
  tests/
```

## Execution Plan
- [x] **Phase 1 — Independence baseline**: implement classical series/parallel redundancy reliability assuming independence.
- [x] **Phase 2 — Physical CCF model**: implement the beta-factor common-cause failure model for physical shared causes, validate against standard reliability engineering textbook examples.
- [x] **Phase 3 — Cyber CCF model**: extend the beta-factor approach to a cyber-specific common-cause factor, grounded in shared-vulnerability reasoning (identical firmware, shared network segment).
- [x] **Phase 4 — Architecture diversity trade-off**: model and compare identical vs. diverse redundant architectures under the combined physical + cyber CCF model.
- [x] **Phase 5 — Case study**: apply the full framework to the shared synthetic system model from the Cyber Attack Impact Modeling project.
- [x] **Phase 6 — Documentation and publishing**: written explanation of the correction this project makes to standard redundancy analysis practice, with the before/after case study as the central result.

## Validation Strategy
- Physical CCF beta-factor model validated against standard published reliability engineering worked examples.
- Independence baseline vs. CCF-adjusted results checked for correct directionality: CCF-adjusted reliability must always be less than or equal to the naive independence estimate, never greater.

## Deliverables
- Public repository with a documented physical + cyber common-cause failure analysis framework
- A case study report quantifying how much redundancy's claimed reliability benefit is reduced once cyber CCF is properly modeled
- Visualizations: reliability-vs-diversity trade-off curves, before/after CCF comparison

## Portfolio Differentiators
- Makes a specific, technically precise, and genuinely underexplored argument (redundancy independence assumption breaks under shared cyber vulnerability) rather than a general "cybersecurity matters" statement — the kind of precise insight that stands out in a technical interview.
- Directly usable to critique or improve real redundancy architecture decisions, making it one of the most immediately applicable projects in the entire portfolio for an actual defense systems engineering role.

## Possible Extensions
- Extend the cyber CCF factor to be informed by the security baselines of NIST SP 800-82 Rev. 3 (free; its OT overlay maps low/moderate/high impact levels to security controls), as a way to translate a system's declared security posture into an estimated cyber CCF factor. ISA/IEC 62443 security levels are the paid industry equivalent and are mentioned by name only.
- Combine with the Unified RBD/Attack Tree project to make cyber CCF an explicit, visualized node type in the unified graph model
