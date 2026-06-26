# Release Criteria

Status: release gate baseline for public and user-facing work

Current local v0.5 candidate notes and checksum: [docs/releases/v0.5.md](docs/releases/v0.5.md).

## Release Boundary

A release is ready only when both boundaries pass:

- Source boundary: repository code, docs, tests, examples, configs, and Action metadata are internally consistent.
- QA artifact boundary: generated package contains only QA-useful files and works from an extracted directory.

## Required Gates

- Automated verifier passes.
- Product repo passes public-export self-scan in paranoid mode.
- Composite Action metadata still uses the tested shell entrypoint.
- user docs describe the CLI, Action, examples, configs, reports, and boundaries accurately.
- License boundary has been reviewed using [docs/license-boundary.md](docs/license-boundary.md), with an owner decision recorded before any external release or additional public distribution.
- Public history risk has been reviewed using [docs/history-risk.md](docs/history-risk.md), with owner acceptance or remediation recorded before any additional tag, release, upload, or public promotion.
- Package artifact excludes generated reports, caches, git metadata, and non-shipping files.
- Product copy preserves the boundary: deterministic preflight reporting, not security/compliance/vulnerability scanning.
- CI verifies the package boundary from a locally generated ZIP without uploading or publicly publishing the release artifact.

## Acceptance Criteria

- `python3 verify_scanner.py` exits zero and prints the expected success line.
- `python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json` exits zero.
- Filename-only history audit commands in [docs/history-risk.md](docs/history-risk.md) have been run, and the owner decision is recorded before additional distribution.
- `bash scripts/package_release.sh v0.5` creates `release/ai-agent-repo-preflight-kit-v0.5.zip`.
- CI `package-boundary` runs `make release-check`, inspects the generated ZIP manifest, extracts the package, and smoke-tests the extracted artifact.
- Extracted package includes `repo_preflight.py`, `action.yml`, `scripts/action_entrypoint.sh`, `scripts/package_release.sh`, `configs/`, `examples/`, `docs/user/`, `docs/dora-ai-readiness.md`, `docs/dora-ai-readiness-profile.md`, `docs/report-schema.md`, `docs/rule-packs.md`, `docs/sarif-output.md`, `README.md`, `README-for-users.md`, `SPEC.md`, `VERIFICATION_PLAN.md`, `PRE_RELEASE_CHECKLIST.md`, `SECURITY.md`, `BLAST_RADIUS_AUDIT.md`, and `verify_scanner.py`.
- Extracted package quickstart commands run without depending on files outside the extracted artifact.
- Extracted package can run `--profile dora-ai-readiness` against a DORA-ready fixture and produce a READY JSON report.

## Verification Commands

```bash
python3 verify_scanner.py
python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json
bash scripts/package_release.sh v0.5
python3 -m zipfile -l release/ai-agent-repo-preflight-kit-v0.5.zip
```

Example extracted-artifact smoke check:

```bash
tmpdir="$(mktemp -d)"
python3 -m zipfile -e release/ai-agent-repo-preflight-kit-v0.5.zip "$tmpdir"
cd "$tmpdir/ai-agent-repo-preflight-kit-v0.5"
python3 verify_scanner.py
python3 repo_preflight.py --repo examples/sample-repo --include-fixtures
```

The sample repo command is expected to report blockers because the fixture is intentionally not ready.

## Remaining-Risk Notes

- The scanner surfaces deterministic preflight signals; it does not certify repository safety.
- False positives are acceptable when they are explainable and easy to suppress through profile choice or rule packs.
- False negatives should be addressed with fixtures and verifier assertions when a deterministic rule can cover them.
- Release artifacts must be checked after packaging because source-tree checks alone do not prove QA artifact contents.
