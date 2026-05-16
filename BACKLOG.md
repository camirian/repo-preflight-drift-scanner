# Backlog

Status: prioritized planning backlog

## P0: v0.4 Buyer Package Smoke Automation

Goal: verify the generated package from an extracted directory, not only from the source tree.

Acceptance criteria:

- Packaging command creates the v0.4 zip.
- Test extracts the zip to a temporary directory.
- Extracted package runs `python3 verify_scanner.py`.
- Extracted package runs the sample repo demo and reports expected blockers.
- Manifest check fails if marketing docs, seller-only release files, generated reports, caches, or git metadata are present.

Verification commands:

```bash
bash scripts/package_release.sh v0.4
python3 -m zipfile -l release/ai-agent-repo-preflight-kit-v0.4.zip
```

## P1: JSON Report Compatibility Notes

Goal: document the stable JSON fields automation users can rely on.

Status: complete for v0.4 baseline; keep this item open only for future schema changes.

Acceptance criteria:

- Document `schema_version`.
- Document `profile`, `decision`, `counts`, `findings`, and `baseline_diff`.
- Mark evidence as optional because privacy controls may remove it.
- Include one minimal sample finding.
- Keep notes aligned with `verify_scanner.py` assertions.

Verification command:

```bash
python3 verify_scanner.py
```

## P1: Rule-Pack Fixture Coverage

Goal: make config behavior safer to change.

Acceptance criteria:

- Add a synthetic fixture or verifier section for custom risky claims.
- Add coverage for custom generated directory names.
- Add coverage for exclusions from a config file.
- Confirm built-in profile behavior still passes.

Verification command:

```bash
python3 verify_scanner.py
```

## P2: Profile Documentation Tightening

Goal: make profile choice obvious for buyers and Action users.

Acceptance criteria:

- Explain when to use `strict`, `docs`, and `public-export`.
- Provide one CLI command and one Action input example for each profile.
- Keep boundary language aligned with buyer docs.

Verification command:

```bash
python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json
```

## P2: SARIF Mapping Review

Goal: ensure SARIF output stays useful without over-claiming precision.

Acceptance criteria:

- Each SARIF result maps to a scanner finding code.
- Severity mapping is documented.
- File locations remain compatible with path privacy controls.
- Verifier confirms SARIF version and non-empty results for blocked fixture scans.

Verification command:

```bash
python3 verify_scanner.py
```

## P3: CI Compatibility Matrix

Goal: document and test supported Python versions once support policy is buyer-facing.

Acceptance criteria:

- State the supported Python version range.
- CI runs the verifier on each supported version.
- Buyer docs mention the same range.

Verification command:

```bash
python3 verify_scanner.py
```
