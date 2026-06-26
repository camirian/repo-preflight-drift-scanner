# CLAUDE.md

Guidance for AI agents and contributors working in this repository. All
statements below are grounded in the repository source as of this writing.

## What this project is

Repo Preflight Drift Scanner is a deterministic, local, read-only,
dependency-free Python tool plus a composite GitHub Action. It scans a
repository for obvious release blockers and AI/process drift signals before
merge, demo, release, or public export, and emits Markdown, JSON, HTML, and
SARIF reports.

Source of truth for behavior: `repo_preflight.py` (single scan engine).
`SPEC.md` states the tool is software (not a template bundle), uses only the
Python standard library, reads the local filesystem only, performs no network
access, and must not read or print secret contents. It is positioned as
deterministic release-gate and public-surface QA infrastructure, not a security,
compliance, or vulnerability scanner and not a replacement for human review.

## Repository layout

- `repo_preflight.py` — the entire CLI scan engine (argparse `main`, profiles,
  finding rules, Markdown/JSON/HTML/SARIF renderers). The only implementation.
- `verify_scanner.py` — the test harness. Not pytest; it is a script of
  `verify_*` functions each returning a bool, wired into `main()` which returns
  `0` on success and `1` on the first failure. Run it directly.
- `action.yml` + `scripts/action_entrypoint.sh` — composite GitHub Action that
  maps inputs to CLI flags. It is a wrapper, not a second scan engine.
- `Makefile` — `test`, `demo`, `package`, `release-check`, `clean` targets.
- `scripts/package_release.sh` — builds the user/release ZIP under `release/`.
- `configs/*.json` — example rule packs passed with `--config`.
- `examples/sample-repo/` — synthetic fixture that intentionally blocks; skipped
  by scans unless `--include-fixtures` is set.
- `docs/` — user docs (`docs/user/`), profile and schema docs, release notes,
  and `docs/report.schema.json` (machine-readable JSON report schema).
- `.github/workflows/ci.yml` — CI: verifier across Python 3.10-3.13, package
  boundary build/extract/smoke, and Action smoke against fixtures.
- Planning/process docs at root: `SPEC.md`, `ARCHITECTURE.md`, `ROADMAP.md`,
  `BACKLOG.md`, `PRODUCT_REQUIREMENTS.md`, `RELEASE_CRITERIA.md`,
  `TEST_STRATEGY.md`, `VERIFICATION_PLAN.md`.

## Build, test, run

Requires Python 3.10-3.13. No third-party dependencies.

- Run all checks: `python3 verify_scanner.py` (or `make test`). Exit `0` passes.
- Demo on the synthetic fixture: `make demo` (writes report files; the fixture
  is designed to block).
- Scan this repo: `python3 repo_preflight.py --repo .`
- List profiles: `python3 repo_preflight.py --list-profiles`
- Build/verify release package: `make release-check VERSION=v0.5`

### Exit codes

- `0`: no blocker findings (decision `READY`).
- `1`: blocker findings present (decision `BLOCKED`), unless suppressed by
  `--fail-on-new-blockers-only` with a matching baseline.
- `2`: a user-facing CLI error (`UserFacingError`).

## Profiles

Defined in `PROFILES` in `repo_preflight.py`: `strict` (default), `docs`,
`dora-ai-readiness`, `public-export`, and `fieldheld-portfolio`. Each toggles a
fixed set of checks (process files, checklist gates, risky claims, drift
markers, generated artifacts, public-export hygiene, secret-bearing filenames,
DORA evidence, Fieldheld evidence). The `dora-ai-readiness` profile reports one
finding per each of seven documented AI capability surfaces (AI stance, data
boundary, AI-accessible context, version-control and rollback path, small-batch
delivery, user focus, internal-platform path); it is evidence-only and claims no
certification or approval.

## Conventions an agent must know

- Determinism and zero dependencies are core invariants. Do not add third-party
  packages. Keep output stable and ordered.
- The scanner never reads or prints secret file contents; it flags
  secret-bearing filenames only. Preserve that boundary.
- Every new rule must ship with a fixture or a `verify_scanner.py` assertion
  (see `ROADMAP.md` and `BACKLOG.md`).
- Generated reports, release ZIPs, and scratch outputs must stay out of git
  source unless they are deliberate release artifacts (`AGENTS.md`). Root report
  files (`*_REPORT.*`, `REPORT.*`, `REPO_PREFLIGHT_REPORT.*`) and `release/` are
  already in `.gitignore`.
- Update user-facing docs when CLI behavior changes.

### The self-scan gate (important)

`verify_scanner.py` runs the strict scanner against this repo (`--repo .`) and
asserts the decision is `READY` with zero blocker, warning, and info findings.
Because the scan walks the working tree, any tracked or in-tree text file you
add is scanned. The strict profile flags, among other things: unchecked
checklist gate lines, process/AI drift marker terms, and risky public claim
phrases (the exact term lists live in `repo_preflight.py`, which is itself
exempt from the content rules). When authoring Markdown in this repo, avoid
those literal trigger substrings and avoid open checklist syntax, or the
self-scan will fail. The single integration check after any change is
`python3 verify_scanner.py`.

