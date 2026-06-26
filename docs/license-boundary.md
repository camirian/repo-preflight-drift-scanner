# License Boundary

Status: release-gate documentation, not legal advice

This document records the current license boundary facts for release review. It does not modify `LICENSE`, `user-license.txt`, package contents, or any granted permissions.

## Current Fact Pattern

- The root repository contains `LICENSE`, which is an MIT license for the repository source and associated documentation.
- The optional release ZIP built by `scripts/package_release.sh` bundles QA-useful files plus `user-license.txt`.
- The release criteria require the QA artifact boundary to be checked separately from the source tree.

## Notes

- The repository source is MIT licensed. Files that appear in any release ZIP are also available under MIT from the source tree; the bundled `user-license.txt` describes packaging terms only and does not revoke rights already granted by the MIT license.
- If you intend to redistribute or relicense, get qualified legal review. This document is an engineering release-control note only.

## Verification Commands

Confirm the source license and user license files exist:

```bash
test -f LICENSE
test -f user-license.txt
```

Build the release ZIP and confirm it includes `user-license.txt`:

```bash
bash scripts/package_release.sh v0.5
python3 -m zipfile -l release/ai-agent-repo-preflight-kit-v0.5.zip | rg 'user-license\.txt'
```

Run release-boundary checks:

```bash
python3 verify_scanner.py
python3 repo_preflight.py --repo . --profile public-export --paranoid --out-md VERIFY_PUBLIC_EXPORT_REPORT.md --out-json VERIFY_PUBLIC_EXPORT_REPORT.json
```

The public-export scan checks release hygiene. It does not decide license compatibility or replace owner/legal review.
