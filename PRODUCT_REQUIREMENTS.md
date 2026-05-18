# Product Requirements

Status: planning baseline for v0.4 readiness and post-v0.4 maintenance

## Goal

Repo Preflight Drift Scanner helps developers and maintainers run a deterministic local preflight before merge, demo, release, public export, or buyer package delivery.

The product outcome is:

```text
repo path -> local scanner or composite GitHub Action -> Markdown/JSON/HTML/SARIF reports -> READY or BLOCKED decision
```

## Users

- Solo developer using AI coding agents who wants a fast release-discipline check.
- Technical founder reviewing an AI-assisted repo before demo, sale, or public upload.
- Maintainer adding a lightweight CI gate to pull requests.
- Buyer of the v0.4 package who needs local CLI setup plus optional GitHub Action setup.

## Core Requirements

- Provide a dependency-free Python CLI that reads a repo path and writes deterministic reports.
- Provide a composite GitHub Action that invokes the same local scanner implementation.
- Support `strict`, `docs`, and `public-export` profiles.
- Emit Markdown and JSON reports by default, with optional HTML and SARIF reports.
- Return a non-zero CLI exit when blocker findings are present.
- Support privacy controls: paranoid mode, no evidence mode, evidence length limits, path rendering modes, and evidence redaction.
- Support rule-pack configuration through JSON files.
- Support baseline diffing from a prior JSON report.
- Document the JSON report schema for automation consumers.
- Keep the v0.4 buyer package useful without requiring external services, accounts, network access, or non-standard-library dependencies.

## Non-Goals

- This is not a security scanner, compliance scanner, vulnerability scanner, license scanner, or code correctness analyzer.
- It must not inspect or print secret file contents.
- It must not modify the scanned repository.
- It must not require a SaaS account or hosted dashboard to produce value.
- It must not make readiness claims beyond deterministic preflight reporting.

## Boundaries

- Runtime boundary: local filesystem only, Python standard library only, read-only scanning.
- Action boundary: composite Action wrapper calls `repo_preflight.py`; it must not fork scan logic.
- Report boundary: Markdown, JSON, HTML, SARIF, and GitHub annotations are outputs; generated reports are not source-of-truth state.
- Package boundary: buyer package contains buyer-useful CLI, Action, examples, configs, and buyer docs only.
- Scope boundary: checks focus on process drift, public-export hygiene, risky claims, release gates, generated artifacts, and secret-bearing filenames.

## Acceptance Criteria

- `python3 repo_preflight.py --repo examples/sample-repo --include-fixtures` returns blockers for the synthetic sample.
- `python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json` returns READY for the product repo.
- `python3 verify_scanner.py` prints `Repo preflight scanner verification passed.`
- `action.yml` uses `runs.using: composite` and calls `scripts/action_entrypoint.sh`.
- v0.4 packaging keeps seller/internal files outside the buyer artifact and preserves buyer setup paths.

## Verification Commands

```bash
python3 verify_scanner.py
python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json
bash scripts/package_release.sh v0.4
```

## Maintenance Impact

- Scanner behavior changes should update `verify_scanner.py`, buyer docs when buyer-facing, and release criteria when packaging changes.
- New profiles or report fields should remain backward-compatible for existing JSON report consumers where practical.
- New rules should prefer deterministic text/path checks and explicit fixture coverage.
