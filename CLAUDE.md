# CLAUDE.md

Redundancy that one cyber attack can defeat. Classical reliability engineering treats
redundant channels as independent, and corrects for shared *physical* causes with
common-cause failure (CCF) models such as the beta factor. This project extends that
correction to shared *cyber* vulnerabilities (identical firmware, a shared network segment, a
shared supply-chain part) that let one attack defeat every channel at once, quantifies how
much of redundancy's claimed benefit survives, and what design diversity buys back, on the
synthetic navigation architecture of the CPS series.
Plan: `CPS-04-common-cause-cyber-failure-redundancy-PLAN.md` (tick the phase checkboxes as
phases land). The navigation system is the one in CPS-02
(`GMCavalheri/cyber-physical-rbd-attack-trees`, package `cpsrbd`) and CPS-01
(`GMCavalheri/cyber-attack-reliability-impact-modeling`, package `cyberrel`); keep component
names and rates consistent with them. The formal derivation (`docs/derivation.md`) is the
groundwork for a research paper, so keep it rigorous.

## Commands
- `uv sync` — install (Python ≥ 3.11; CI runs 3.11, 3.12 and 3.13)
- `uv run pytest --cov` — tests with the 90 % coverage gate
- `uv run ruff check .` and `uv run ruff format --check .` — lint/format. Ruff also formats
  the ```python blocks inside Markdown, so run it after editing docs too
- `uv run mypy` — strict type check of `src/`
- `uv run python validation/<script>.py` — regenerate one phase's tables
  (`validation/results/`) and figures (`docs/figures/`); `validation/run_all.py` runs them all
- `uv run python notebooks/build_notebooks.py` — regenerate and execute the notebooks

## Layout
- `src/cyberccf/` — single package; subpackages mirror the plan:
  `independence_baseline` (basic events, series/parallel/k-of-n structures, exact
  quantification by factoring, the navigation system), `physical_ccf_beta_factor` (beta
  factor, alpha factor, MGL), `cyber_ccf_model` (channel attributes, shared-vulnerability
  events, the cyber beta factor), `architecture_diversity_tradeoff`, `case_study_application`,
  `time_dependent` (Markov availability/MTBF, Monte Carlo oracle), `security_posture`
  (NIST SP 800-82 posture to a cyber-beta range); plus `plotting.py`.
- `src/cyberccf/data/` — parameter tables (CSV); every value is labelled an assumption or
  carries its source.
- `tests/` — pytest + Hypothesis. `validation/` — one script per phase, `results/` tables.
- `docs/` — theory note per module, `scope.md`, `derivation.md`, `related-work.md`,
  `report.md`; `docs/lessons/` is the course (keep its numbers in sync with
  `validation/results/`). `notebooks/` — one executed demo per lesson.

## Conventions
- Time is in hours; the mission is 10 h, as in CPS-01/02. Physical failures are exponential
  (constant rate λ). A probability over a mission is $q = 1 - e^{-\lambda t}$.
- A common-cause event is a basic event of its own that fails every member of its group at
  once; it is independent of the members' individual failures. This is the standard
  basic-event formulation (NUREG/CR-5485), so CCF and independence share one exact engine.
- A shared cyber vulnerability is modelled by its **effect**: an event, with an illustrative
  rate, that defeats every channel holding the same attribute value. Never present such a
  rate as field data: it is an explicit, illustrative assumption explored by sensitivity.
- Simulations take a seeded `numpy.random.Generator`.
- Exact results (closed forms) are compared with tolerance 1e-12 (relative where values are
  small); Monte Carlo against its own confidence interval.

## Scope (public repo)
- Synthetic system and public methodology only (NUREG/CR-5485 and CR-6268, the beta-factor
  literature, NIST SP 800-82 Rev. 3). ISA/IEC 62443 and IEC 61508 are paid standards: name
  them, cite them only through free secondary sources. See `docs/scope.md`.
- No exploit procedures and no real product vulnerabilities.
- Never mention the author's employer or day job in any file, commit message or doc.

## Docs (GitHub-rendered math)
- Display equations go in ```` ```math ```` fences (no Markdown processing inside).
- Inline `$...$` is processed as Markdown first: no `\,` or `\;`, no `\\` row breaks, and no
  `_` right after `}` `)` `]`. `tests/test_docs.py` guards this.

## Testing rules
- Every test asserts against a closed-form result, an independent oracle (CPS-02's `cpsrbd`,
  CPS-01's `cyberrel`, brute-force state enumeration, Monte Carlo) or a cited published
  value; name the source in a comment.
- Never loosen a tolerance to make a failing test pass without explaining why.
- Properties that must hold for every parameter set (common cause never makes a system more
  reliable, diversity never makes it less reliable) are Hypothesis tests.

## Workflow
- Commit small logical changes directly to `main`; push after ruff, mypy and pytest pass,
  each run as its own command (no pipes: a pipe hides the exit code). Stage explicit paths.
- Each phase lands as code + tests, then validation results, then its lesson in
  `docs/lessons/` as a separate commit. Confirm CI is green after each push.
