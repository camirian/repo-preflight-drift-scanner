# Test Strategy

Status: current verification strategy with expansion path

## Test Goals

- Prove the scanner catches known release-discipline blockers in a synthetic repo.
- Prove the product repo passes strict and public-export self-scans.
- Prove reports are written in the expected formats.
- Prove secret-bearing fixture content is not leaked into reports.
- Prove the composite Action wrapper follows CLI behavior.
- Prove privacy controls, baseline diffing, docs profile, and Python compilation remain intact.

## Current Automated Verification

Primary command:

```bash
python3 verify_scanner.py
```

The verifier covers:

- Synthetic blocked fixture scan.
- Markdown, JSON, HTML, and SARIF report generation.
- Required finding codes for missing process file, secret-bearing filename, unchecked release gate, risky public claim, generated artifact directory, and drift marker.
- GitHub annotation output.
- Action entrypoint report-only behavior.
- Baseline diff with no new findings against an identical baseline.
- Paranoid mode path and evidence suppression.
- Strict self-scan READY decision.
- Public-export self-scan READY decision.
- Docs profile READY decision with `configs/founder-strict.json`.
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

## Buyer Artifact Checks

For v0.4 buyer package readiness:

```bash
bash scripts/package_release.sh v0.4
```

Then inspect the generated zip manifest and extracted artifact before upload. The artifact should contain only buyer-useful files and should support the buyer quickstart from the extracted directory.

## Acceptance Criteria

- `python3 verify_scanner.py` passes before release.
- Product repo public-export scan returns READY.
- Local Action entrypoint report-only smoke test exits zero.
- Buyer package extraction smoke test can run the local demo without source-tree-only paths.
- No test requires external network access or third-party dependencies.

## Expansion Path

- Add dedicated fixtures for each profile.
- Add JSON schema compatibility checks for report consumers.
- Add package extraction smoke automation to prevent source-tree-only packaging errors.
- Add CI matrix coverage for supported Python versions if compatibility becomes buyer-facing.
