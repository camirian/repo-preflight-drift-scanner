# Test Strategy

Status: current verification strategy with expansion path

## Test Goals

- Prove the scanner catches known release-discipline blockers in a synthetic repo.
- Prove the product repo passes strict and public-export self-scans.
- Prove reports are written in the expected formats.
- Prove focused profile fixtures keep `docs` lower-noise, `dora-ai-readiness` evidence-backed, and `public-export` conservative.
- Prove secret-bearing fixture content is not leaked into reports.
- Prove the composite Action wrapper follows CLI behavior.
- Prove privacy controls, baseline diffing, baseline-aware gating, docs profile, and Python compilation remain intact.
- Prove JSON reports include a schema version and match the documented machine-readable schema contract for automation consumers.
- Prove SARIF output remains compatible with documented level and rule mapping.
- Prove common CLI input errors fail with concise user-facing messages.
- Prove the verifier passes across the supported Python range, Python 3.10 through 3.13.

## Current Automated Verification

Primary command:

```bash
python3 verify_scanner.py
```

CI runs the verifier against Python 3.10, 3.11, 3.12, and 3.13.

The verifier covers:

- Synthetic blocked fixture scan.
- Markdown, JSON, HTML, and SARIF report generation.
- Focused output compatibility across JSON, Markdown, HTML, and SARIF for profile fixtures.
- Machine-readable JSON report schema artifact structure checks.
- JSON report contract checks for generated reports, including baseline diff output.
- DORA-ready and DORA-weak fixtures for `dora-ai-readiness`.
- Composite Action smoke coverage for the DORA AI readiness profile.
- DORA secret-bearing fixture filename coverage that must not leak content or block the evidence-only profile.
- Required finding codes for missing process file, secret-bearing filename, unchecked release gate, risky public claim, generated artifact directory, and drift marker.
- GitHub annotation output.
- Action entrypoint report-only behavior, fail-on-blockers behavior, and baseline-aware new-blocker gating.
- Baseline diff with no new findings against an identical baseline, new blockers, and new non-blockers.
- Paranoid mode path and evidence suppression.
- Strict self-scan READY decision.
- Public-export self-scan READY decision.
- Docs profile READY decision with `configs/founder-strict.json`.
- Rule-pack behavior for custom required files, terms, generated dirs, secret-bearing filenames, and exclusions.
- CLI error handling for invalid config JSON, unknown config keys, invalid redaction regex, missing baseline files, and baseline-aware gates without a baseline.
- release package boundary, reproducible ZIP bytes, and extracted-artifact smoke checks.
- Extracted release package DORA AI readiness smoke coverage.
- `py_compile` for `repo_preflight.py` and `verify_scanner.py`.

## Manual Smoke Checks

Run the local demo:

```bash
python3 repo_preflight.py --repo examples/sample-repo --include-fixtures --out-md REPORT.md --out-json REPORT.json --out-html REPORT.html --out-sarif REPORT.sarif
```

Run the product public-export scan:

```bash
python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json
```

Run the Action entrypoint locally:

```bash
GITHUB_ACTION_PATH="$PWD" \
INPUT_REPO="examples/sample-repo" \
INPUT_INCLUDE_FIXTURES="true" \
INPUT_GITHUB_ANNOTATIONS="true" \
INPUT_FAIL_ON_BLOCKERS="false" \
scripts/action_entrypoint.sh
```

## QA artifact Checks

For the current release package candidate:

```bash
bash scripts/package_release.sh
```

Then inspect the generated zip manifest and extracted artifact before upload. The artifact should contain only QA-useful files and should support the user quickstart from the extracted directory.

## Acceptance Criteria

- `python3 verify_scanner.py` passes before release.
- Product repo public-export scan returns READY.
- DORA-ready fixture returns READY with seven evidence findings.
- DORA-weak fixture returns BLOCKED with seven missing-evidence findings.
- Action DORA profile smoke test exits zero for a DORA-ready fixture.
- Local Action entrypoint report-only smoke test exits zero.
- Baseline-aware CLI and Action gates fail only for new blockers when a baseline is supplied.
- release package extraction smoke test can run the local demo without source-tree-only paths.
- release package extraction smoke test can run a DORA-ready scan from the extracted artifact.
- No test requires external network access or third-party dependencies.

## Expansion Path

- Add more focused fixtures when new profiles or output formats are introduced.
