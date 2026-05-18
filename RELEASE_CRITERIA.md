# Release Criteria

Status: release gate baseline for public and buyer-facing work

Current local v0.4 candidate notes and checksum: [docs/releases/v0.4.md](docs/releases/v0.4.md).

## Release Boundary

A release is ready only when both boundaries pass:

- Source boundary: repository code, docs, tests, examples, configs, and Action metadata are internally consistent.
- Buyer artifact boundary: generated package contains only buyer-useful files and works from an extracted directory.

## Required Gates

- Automated verifier passes.
- Product repo passes public-export self-scan in paranoid mode.
- Composite Action metadata still uses the tested shell entrypoint.
- Buyer docs describe the CLI, Action, examples, configs, reports, and boundaries accurately.
- License boundary has been reviewed using [docs/license-boundary.md](docs/license-boundary.md), with an owner decision recorded before any paid release or additional public distribution.
- Public history risk has been reviewed using [docs/history-risk.md](docs/history-risk.md), with owner acceptance or remediation recorded before any additional tag, release, upload, or public promotion.
- Package artifact excludes generated reports, caches, git metadata, marketing material, and seller-only files.
- Product copy preserves the boundary: deterministic preflight reporting, not security/compliance/vulnerability scanning.
- CI verifies the package boundary from a locally generated ZIP without uploading or publicly publishing the release artifact.

## Acceptance Criteria

- `python3 verify_scanner.py` exits zero and prints the expected success line.
- `python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json` exits zero.
- Filename-only history audit commands in [docs/history-risk.md](docs/history-risk.md) have been run, and the owner decision is recorded before additional distribution.
- `bash scripts/package_release.sh v0.4` creates `release/ai-agent-repo-preflight-kit-v0.4.zip`.
- CI `package-boundary` runs `make release-check`, inspects the generated ZIP manifest, extracts the package, and smoke-tests the extracted artifact.
- Extracted package includes `repo_preflight.py`, `action.yml`, `scripts/action_entrypoint.sh`, `scripts/package_release.sh`, `configs/`, `examples/`, `docs/buyer/`, `docs/report-schema.md`, `docs/rule-packs.md`, `docs/sarif-output.md`, `README.md`, `README-for-buyers.md`, `SPEC.md`, `VERIFICATION_PLAN.md`, `PRE_RELEASE_CHECKLIST.md`, `SECURITY.md`, `BLAST_RADIUS_AUDIT.md`, `buyer-license.txt`, and `verify_scanner.py`.
- Extracted package quickstart commands run without depending on files outside the extracted artifact.

## Verification Commands

```bash
python3 verify_scanner.py
python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json
bash scripts/package_release.sh v0.4
python3 -m zipfile -l release/ai-agent-repo-preflight-kit-v0.4.zip
```

Example extracted-artifact smoke check:

```bash
tmpdir="$(mktemp -d)"
python3 -m zipfile -e release/ai-agent-repo-preflight-kit-v0.4.zip "$tmpdir"
cd "$tmpdir/ai-agent-repo-preflight-kit-v0.4"
python3 verify_scanner.py
python3 repo_preflight.py --repo examples/sample-repo --include-fixtures
```

The sample repo command is expected to report blockers because the fixture is intentionally not ready.

## Remaining-Risk Notes

- The scanner surfaces deterministic preflight signals; it does not certify repository safety.
- False positives are acceptable when they are explainable and easy to suppress through profile choice or rule packs.
- False negatives should be addressed with fixtures and verifier assertions when a deterministic rule can cover them.
- Release artifacts must be checked after packaging because source-tree checks alone do not prove buyer artifact contents.
