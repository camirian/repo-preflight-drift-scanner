# Roadmap

Status: actionable planning baseline

## Current Baseline

- Deterministic local Python CLI exists in `repo_preflight.py`.
- Composite GitHub Action exists in `action.yml` and calls `scripts/action_entrypoint.sh`.
- Reports include Markdown, JSON, HTML, and SARIF.
- Profiles include `strict`, `docs`, `dora-ai-readiness`, and `public-export`.
- Verification is centralized in `verify_scanner.py` and CI should run that verifier.
- v0.5 release package candidate readiness is represented by `scripts/package_release.sh`, user docs, examples, configs, and staged release output.

## v0.4 Release Readiness

Goal: make the release package safe to share and clear to use.

Acceptance criteria:

- `python3 verify_scanner.py` passes.
- `bash scripts/package_release.sh v0.4` creates the package directory and zip.
- Extracted package contains QA-useful files: CLI, Action metadata, action entrypoint, configs, examples, user docs, README, license, and verifier.
- Extracted package contains the JSON report schema referenced by user docs.
- Extracted package excludes generated reports, caches, git metadata, and non-shipping files.
- user quickstart can be followed from the extracted artifact.

Verification commands:

```bash
python3 verify_scanner.py
bash scripts/package_release.sh v0.4
python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json
```

## Near-Term Product Hardening

Goal: reduce false positives while keeping deterministic behavior.

Acceptance criteria:

- Every new rule has a fixture or verifier assertion.
- Rule-pack behavior is documented through a minimal example.
- `docs` profile remains low-noise for template-heavy documentation.
- `public-export` profile remains conservative for public repo and package checks.
- SARIF output maps cleanly to deterministic finding codes without over-claiming precision.

Verification commands:

```bash
python3 verify_scanner.py
python3 repo_preflight.py --repo . --profile docs --config configs/founder-strict.json --out-md VERIFY_DOCS_REPORT.md --out-json VERIFY_DOCS_REPORT.json
```

## CI And Action Reliability

Goal: keep CLI and GitHub Action behavior aligned.

Acceptance criteria:

- Action entrypoint passes inputs through to the CLI without changing scan semantics.
- Report-only mode exits zero when `fail-on-blockers` is false.
- Fail-on-blockers mode exits non-zero when blocker findings exist.
- GitHub annotations appear when enabled.

Verification commands:

```bash
python3 verify_scanner.py
GITHUB_ACTION_PATH="$PWD" INPUT_REPO="examples/sample-repo" INPUT_INCLUDE_FIXTURES="true" INPUT_FAIL_ON_BLOCKERS="false" scripts/action_entrypoint.sh
```

## DORA AI Readiness Mode

Goal: help AI-assisted teams see whether their repo documents the seven DORA AI capability surfaces before they treat AI acceleration as an operating advantage.

Acceptance criteria:

- `--profile dora-ai-readiness` reports explicit evidence for AI stance, data boundary, AI-accessible context, version-control and rollback path, small-batch delivery, user or user signal, and internal-platform verification.
- Missing evidence creates blocker findings.
- Present evidence creates info findings with line references.
- The profile remains deterministic and does not claim DORA certification, compliance approval, security, public-export safety, secret hygiene, or production readiness.

Verification command:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/repo-preflight-pycache python3 verify_scanner.py
```

## Post-v0.4 Candidates

- Add focused fixtures for new profiles and output formats as they are introduced.
- Add schema notes for JSON report consumers.
- Add a small compatibility matrix for Python versions used in CI.
- Extend user-package smoke tests as new user workflows are added.
- Improve SARIF coverage only where it maps cleanly to deterministic findings.
