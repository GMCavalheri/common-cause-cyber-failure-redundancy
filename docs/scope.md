# Scope and modelling boundaries

This repository is a **reliability methodology and software** project. It asks one question
about redundant architectures: how much of the benefit claimed for redundancy survives once
the channels can fail *together*, from a shared physical cause or from a shared cyber
vulnerability. Everything in it is meant to be safe to publish, and these rules keep it that
way.

## What is modelled

* **A synthetic system.** The navigation system (two embedded GNSS/INS units, two power
  buses, a dual-channel data bus and a mission computer) is the generic, defense-
  *representative* architecture of CPS-02 (GMCavalheri/cyber-physical-rbd-attack-trees) and
  CPS-01 (GMCavalheri/cyber-attack-reliability-impact-modeling), with the same failure rates,
  copied with their basis into
  [`system_parameters.csv`](../src/cyberccf/data/system_parameters.csv). It does not describe
  any real platform, product, operator or programme.
* **Physical failures** as constant-rate events, and **physical common cause** (a shared
  supply, a shared environment, a shared design or maintenance error) through the standard
  beta-factor, alpha-factor and multiple Greek letter models of the public nuclear
  probabilistic-risk-assessment literature (NUREG/CR-5485).
* **Shared cyber vulnerabilities by their effect only.** Each redundant channel carries a few
  attributes: its firmware or software load, its network segment and its supply-chain source.
  A shared vulnerability is an event, at an illustrative rate, that defeats **every channel
  holding the same attribute value**, and nothing else is said about it. Which vulnerability,
  how it would be found or exploited, on what product: all of that is **out of scope**. No
  vulnerabilities, procedures, tools, protocol details or configurations appear anywhere, and
  no real product vulnerability (CVE or advisory) is used as a parameter.
* **Security posture** only through the public NIST SP 800-82 Rev. 3 OT overlay (low,
  moderate and high impact levels), mapped to a *range* of the cyber common-cause parameter
  by a rubric whose every weight is a labelled assumption. ISA/IEC 62443 and IEC 61508 are
  paid standards: they are named, and cited only through free secondary sources.

## Why this is the right boundary

A reliability model needs only to know *which channels fail together and how often*. Whether
two channels fail together because one power bus failed or because one firmware image was
compromised, the block diagram sees the same thing: one event that removes both. Modelling the
vulnerability by that effect costs the analysis nothing, and it is the level at which a
reliability engineer can act (diversify the firmware, split the network, dual-source the
part) without knowing anything an attacker would need.

## Numbers

* Physical failure rates are the CPS series' illustrative assumptions.
* Physical beta factors are within the ranges reported in the public CCF literature and are
  labelled as such where they are used.
* **Cyber rates and cyber beta factors have no field-data basis.** They are explicit,
  illustrative assumptions, and every conclusion that depends on them is shown across a range
  (sensitivity analysis), never at a single point. This is the main honest limit of the
  project, and of the research question behind it.

## What is out of scope

* Real aircraft, avionics or navigation products, and any real reliability or incident data.
* Anything about gaining access to a system; offensive tooling of any kind.
* A complete cyber risk model. Only one failure mode is modelled: several redundant channels
  defeated at once because they share something. Attacks that defeat one channel, or that
  corrupt data without stopping it (see CPS-03), are other projects.
