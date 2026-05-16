# Roadmap

Status: actionable planning baseline

## Current Baseline

- Deterministic local Python CLI exists in `repo_preflight.py`.
- Composite GitHub Action exists in `action.yml` and calls `scripts/action_entrypoint.sh`.
- Reports include Markdown, JSON, HTML, and SARIF.
- Profiles include `strict`, `docs`, and `public-export`.
- Verification is centralized in `verify_scanner.py` and CI should run that verifier.
- v0.4 buyer package readiness is represented by `scripts/package_release.sh`, buyer docs, examples, configs, and staged release output.

## v0.4 Release Readiness

Goal: make the buyer package safe to upload and clear to use.

Acceptance criteria:

- `python3 verify_scanner.py` passes.
- `bash scripts/package_release.sh v0.4` creates the package directory and zip.
- Extracted package contains buyer-useful files: CLI, Action metadata, action entrypoint, configs, examples, buyer docs, README, license, and verifier.
- Extracted package contains the JSON report schema referenced by buyer docs.
- Extracted package excludes marketing docs, generated reports, caches, git metadata, and seller-only release material.
- Buyer quickstart can be followed from the extracted artifact.

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

## Post-v0.4 Candidates

- Add focused fixtures for each profile and output format.
- Add schema notes for JSON report consumers.
- Add a small compatibility matrix for Python versions used in CI.
- Extend buyer-package smoke tests as new buyer workflows are added.
- Improve SARIF coverage only where it maps cleanly to deterministic findings.
