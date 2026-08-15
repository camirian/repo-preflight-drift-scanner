# Repo Preflight Drift Scanner Agent Instructions

This is a public repository for deterministic repo-audit tooling.

## Mission

The scanner exists to catch repository-level drift before merge, demo, release, or publication. Release hygiene is not enough: a repository can be clean, well tested, and still implement the wrong product. Mission/source fidelity is therefore a first-class scanner concern.

## Prime rules

- Keep generated reports, release zips, and scratch outputs out of source unless they are deliberate release artifacts.
- Do not commit customer data, private repo contents, secrets, or local scan outputs.
- Update documentation when CLI behavior changes.
- Run focused CLI checks before claiming release readiness.
- Keep checks deterministic and local; do not add an LLM semantic judge.
- Distinguish **verification** (implementation matches its contract) from **validation** (the contract is grounded in the user's intended mission/source).
- A clean release/process scan must never be described as proof that the repository is building the right product.

## Mission-fidelity capability

`mission_preflight.py` validates an explicit repository contract using:

- `.mission/owner_constraints.json`;
- `.mission/features.json`;
- a canonical `AGENTS.md` (or configured equivalent);
- product roots and feature implementation paths;
- source-evidence kinds;
- invention/novelty budget;
- owner authorization for augmentation;
- user/domain confirmation for default-workflow changes;
- separation of mission-contract changes from product behavior when Git history is available.

It must block at least these failure modes:

- user-visible behavior with no originating source/requirement trace;
- mirrored behavior justified only by derived analysis;
- agent-authored design self-authorizing implementation;
- augmentation under a zero invention budget without explicit owner authorization;
- default workflow changes without user/domain confirmation;
- product implementation paths not covered by a feature trace;
- tool-specific instructions explicitly allowed to override canonical agent doctrine;
- mission/governance and product behavior changed in one branch.

## Boundary

The scanner checks **structure and explicit evidence contracts**, not truth semantics. It may establish that a feature cites a source artifact; it cannot prove that the cited artifact really authorizes the feature. Human/domain validation remains required.

## Adversarial verification

Any new mission-fidelity rule must ship with a case designed to defeat it. Run:

```bash
python3 verify_mission_preflight.py
```

before claiming the mission preflight works.

The ordinary scanner verification remains required for changes to `repo_preflight.py`.

## Change discipline

Before broad changes:

1. Identify the exact failure mode being prevented.
2. Prefer the smallest deterministic rule that detects it.
3. Add a positive case so the scanner does not block correctly governed repositories.
4. Add an adversarial case that previously slipped through.
5. Keep public/private artifact boundaries intact.
6. Report both what the scanner proves and what it explicitly cannot prove.
